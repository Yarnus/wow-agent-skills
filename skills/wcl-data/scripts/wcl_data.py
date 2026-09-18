#!/usr/bin/env python3
"""Retrieve scoped Retail raid facts from the official Warcraft Logs API."""
import argparse
import base64
import http.client
import json
import math
import os
import re
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://www.warcraftlogs.com/api/v2/client"
TOKEN_URL = "https://www.warcraftlogs.com/oauth/token"
REPORT_QUERY = """
query ReportIndex($code: String!) {
  reportData { report(code: $code, allowUnlisted: true) {
    code revision title visibility startTime endTime
    zone { id encounters { id } difficulties { id sizes } }
    masterData { gameVersion actors { id gameID name server type subType } }
    fights { id encounterID name startTime endTime kill inProgress difficulty
             keystoneLevel friendlyPlayers }
  } }
}
"""
EVENT_QUERY = """
query ScopedEvents($code: String!, $fightIDs: [Int], $startTime: Float!, $endTime: Float!,
                   $filterExpression: String!) {
  reportData { report(code: $code, allowUnlisted: true) { code revision
    events(fightIDs: $fightIDs, startTime: $startTime, endTime: $endTime,
           filterExpression: $filterExpression, dataType: All, limit: 10000,
           useActorIDs: true, useAbilityIDs: true, includeResources: true) {
      data nextPageTimestamp
    }
  } }
}
"""
EVENT_TYPES = {"damage", "cast", "applydebuff", "removedebuff"}

REVISION_QUERY = """
query ReportRevision($code: String!) {
  reportData { report(code: $code, allowUnlisted: true) { code revision } }
}
"""


class DataError(Exception):
    pass


class Client:
    def __init__(self):
        client_id = os.environ.get("WCL_CLIENT_ID")
        secret = os.environ.get("WCL_CLIENT_SECRET")
        if not client_id and not secret:
            client_id = os.environ.get("WCL_ID")
            secret = os.environ.get("WCL_SECRET")
        if not client_id or not secret:
            raise DataError("Set WCL_CLIENT_ID and WCL_CLIENT_SECRET (or WCL_ID and WCL_SECRET).")
        basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
        payload = self.request(urllib.request.Request(
            TOKEN_URL, data=b"grant_type=client_credentials",
            headers={"Authorization": f"Basic {basic}",
                     "Content-Type": "application/x-www-form-urlencoded"}))
        self.token = payload["access_token"]

    def request(self, request):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
            if status == 429:
                raise DataError("WCL rate limit reached; retry later. No evidence published.") from exc
            raise DataError(f"WCL HTTP {status}; no evidence published.") from exc
        except (OSError, http.client.HTTPException, ValueError) as exc:
            raise DataError("WCL transport failed or returned invalid JSON; no evidence published.") from exc

    def report(self, query, variables):
        payload = self.request(urllib.request.Request(
            API_URL, data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}))
        if payload.get("errors"):
            raise DataError("WCL GraphQL request failed.")
        value = payload["data"]["reportData"]["report"]
        if not isinstance(value, dict):
            raise DataError("Report is inaccessible.")
        return value


def report_code(value):
    if "://" in value:
        url = urllib.parse.urlsplit(value)
        if url.scheme != "https" or url.netloc not in {"www.warcraftlogs.com", "warcraftlogs.com", "cn.warcraftlogs.com"}:
            raise DataError("Use an official Retail WCL report URL.")
        match = re.fullmatch(r"/reports/([A-Za-z0-9]+)/?", url.path)
        value = match[1] if match else ""
    if not re.fullmatch(r"[A-Za-z0-9]+", value):
        raise DataError("Invalid report code.")
    return value


def check_revision(client, code, revision):
    current = client.report(REVISION_QUERY, {"code": code})
    if current.get("code") != code or current.get("revision") != revision:
        raise DataError("Report identity or Revision changed during retrieval.")


def index(client, code):
    data = client.report(REPORT_QUERY, {"code": code})
    if data["code"] != code or type(data["revision"]) is not int:
        raise DataError("Invalid Report identity or Revision.")
    if data["visibility"] not in {"public", "unlisted"} or data["masterData"]["gameVersion"] != 1:
        raise DataError("Only public or unlisted Retail reports are supported.")
    zone = data["zone"]
    if not any(max(d["sizes"], default=0) > 5 for d in zone["difficulties"]):
        raise DataError("Only reports with an identified raid zone are supported.")
    raid_difficulties = {d["id"] for d in zone["difficulties"]}
    encounters = {e["id"] for e in zone["encounters"]}
    actors = {a["id"]: a for a in data["masterData"]["actors"]}
    if (len(actors) != len(data["masterData"]["actors"])
            or any(type(i) is not int or (i <= 0 and not (i == -1 and actors[i]["type"] == "NPC"
                                                       and actors[i].get("gameID") == 0)) for i in actors)):
        raise DataError("Invalid or duplicate actor IDs.")
    for actor in actors.values():
        game_id = actor.get("gameID")
        if actor["type"] == "NPC" and game_id is not None and (type(game_id) is not int or game_id < 0):
            raise DataError("Malformed NPC game ID.")
    if not finite_number(data["startTime"]) or not finite_number(data["endTime"]):
        raise DataError("Invalid Report time range.")
    attempts = []
    seen_fights = set()
    for fight in data["fights"]:
        if (type(fight["id"]) is not int or fight["id"] <= 0 or fight["id"] in seen_fights
                or not finite_number(fight["startTime"]) or not finite_number(fight["endTime"])
                or not 0 <= fight["startTime"] <= fight["endTime"] <= data["endTime"] - data["startTime"]):
            raise DataError("Invalid or duplicate Boss Attempt identity/time range.")
        seen_fights.add(fight["id"])
        if (fight["encounterID"] not in encounters or fight["inProgress"] is not False
                or fight["difficulty"] not in raid_difficulties or fight["keystoneLevel"] is not None):
            continue
        participants = []
        for actor_id in fight["friendlyPlayers"]:
            actor = actors[actor_id]
            if actor["type"] != "Player":
                raise DataError("Participant ID does not identify a player.")
            participants.append({"actor_id": actor_id, "name": actor["name"],
                                 "server": actor.get("server"), "class": actor.get("subType")})
        attempts.append({"fight_id": fight["id"], "encounter_id": fight["encounterID"],
                         "name": fight["name"], "difficulty_id": fight["difficulty"],
                         "start_ms": fight["startTime"], "end_ms": fight["endTime"],
                         "kill": fight["kill"], "participants": participants})
    check_revision(client, code, data["revision"])
    return {
        "status": "ok", "identity": {"report_code": code, "report_revision": data["revision"]},
        "source": {"provider": "Warcraft Logs", "endpoint": API_URL,
                   "url": f"https://www.warcraftlogs.com/reports/{code}",
                   "time_basis": "report_relative_ms", "report_start_unix_ms": data["startTime"],
                   "id_namespaces": {"actor_id": "WCL report-local actor ID", "encounter_id": "WCL encounter ID",
                                     "abilityGameID": "WoW Spell ID", "npc_id": "WoW NPC ID",
                                     "sourceID/targetID": "WCL report-local actor ID"}},
        "applicability": {"game_branch": "Retail", "zone_id": zone["id"], "build": None},
        "coverage": {"scope": "completed_raid_attempt_index", "revision_consistent": True,
                     "whole_attempt_events": False, "complete_bundle": False,
                     "excluded_fights": len(data["fights"]) - len(attempts)},
        "display": {"matched": len(attempts), "returned": len(attempts), "truncated": False},
        "actors": [{"actor_id": a["id"], "name": a["name"], "type": a["type"],
                    "npc_id": a.get("gameID") if a["type"] == "NPC" and a.get("gameID") != 0 else None,
                    "server": a.get("server")} for a in actors.values()],
        "attempts": attempts,
    }


def finite_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def pages(client, identity, fight_id, start, end, expression, event_type=None):
    events = []
    count = 0
    cursor = start
    while True:
        value = client.report(EVENT_QUERY, {"code": identity["report_code"], "fightIDs": [fight_id],
                              "startTime": cursor, "endTime": end, "filterExpression": expression})
        if value["code"] != identity["report_code"] or value["revision"] != identity["report_revision"]:
            raise DataError("Report identity or Revision changed during pagination.")
        page = value["events"]
        if not isinstance(page, dict) or not isinstance(page.get("data"), list) or "nextPageTimestamp" not in page:
            raise DataError("Malformed event page or missing pagination cursor.")
        next_cursor = page["nextPageTimestamp"]
        if next_cursor is not None and (not finite_number(next_cursor) or not cursor < next_cursor <= end):
            raise DataError("Pagination cursor did not advance within the query range.")
        for event in page["data"]:
            if (not isinstance(event, dict) or not finite_number(event.get("timestamp"))
                    or not cursor <= event["timestamp"] <= end or not isinstance(event.get("type"), str)):
                raise DataError("Malformed event or timestamp outside query range.")
            for key in ("sourceID", "targetID"):
                if key in event and type(event[key]) is not int:
                    raise DataError("Malformed event actor ID.")
            if ("abilityGameID" in event and (type(event["abilityGameID"]) is not int
                                               or event["abilityGameID"] < 0)):
                raise DataError("Malformed event ability game ID.")
            if event["type"] == "death" and type(event.get("targetID")) is not int:
                raise DataError("Death event is missing its target actor ID.")
            if event["type"] == "death" and "feign" in event and type(event["feign"]) is not bool:
                raise DataError("Malformed death event feign flag; expected a boolean when present.")
            matches = event_type is None or event["type"] == event_type
            if not matches or (events and event["timestamp"] < events[-1]["timestamp"]):
                raise DataError("Event identity/filter mismatch or unordered events.")
            events.append(event)
        count += 1
        if next_cursor is None:
            return events, {"pages": count, "terminated_explicitly": True}
        cursor = next_cursor


def classify_deaths(events, actor_ids=None):
    if actor_ids is not None:
        events = [event for event in events if event.get("targetID") in actor_ids]
    excluded_feign = sum(event.get("feign") is True for event in events)
    missing_feign = sum("feign" not in event for event in events)
    candidates = [event for event in events if event.get("feign") is not True]
    return candidates, {
        "candidate_count": len(candidates), "excluded_feign_count": excluded_feign,
        "missing_feign_count": missing_feign, "policy": "exclude_explicit_true"}


def death_records(events):
    ordinals = {}
    records = []
    for event in events:
        actor_id = event["targetID"]
        ordinals[actor_id] = ordinals.get(actor_id, 0) + 1
        records.append({"actor_id": actor_id, "death": ordinals[actor_id],
                        "timestamp": event["timestamp"]})
    return records


def death_window(client, code, args):
    result = index(client, code)
    if args.expected_revision is not None and result["identity"]["report_revision"] != args.expected_revision:
        raise DataError("Expected Report Revision does not match the retrieved report.")
    fight = next((f for f in result["attempts"] if f["fight_id"] == args.fight_id), None)
    if fight is None:
        raise DataError("Fight ID does not identify a supported Boss Attempt.")
    player = next((p for p in fight["participants"] if p["actor_id"] == args.actor_id), None)
    if player is None:
        raise DataError("Actor ID is not a participant of this Boss Attempt.")
    result.pop("attempts")
    result["identity"].update({"fight_id": args.fight_id, "actor_id": args.actor_id})
    result["attempt"] = fight
    result["participant"] = player
    result["source"]["url"] += f"#fight={args.fight_id}&source={args.actor_id}"
    deaths, death_pagination = pages(client, result["identity"], args.fight_id, fight["start_ms"],
                                    fight["end_ms"], "type = 'death'", "death")
    deaths, classification = classify_deaths(deaths, {args.actor_id})
    result["death_classification"] = classification
    result["deaths"] = [{"death": i + 1, "timestamp": event["timestamp"]}
                         for i, event in enumerate(deaths)]
    guarded = args.expected_revision is not None
    if guarded:
        check_revision(client, code, result["identity"]["report_revision"])
        if not deaths:
            raise DataError("Expected death ordinal does not identify a candidate; refusing fallback.")
    if not deaths or (len(deaths) > 1 and args.death is None):
        if not guarded:
            check_revision(client, code, result["identity"]["report_revision"])
        result["status"] = "no_death" if not deaths else "needs_selection"
        result["coverage"] = {"scope": "participant_deaths", "death_pagination": death_pagination,
                              "death_search_scope": "all_actor_deaths", "actor_filter": "local targetID",
                              "death_search_window_ms": [fight["start_ms"], fight["end_ms"]],
                              "query_complete": False, "revision_consistent": True,
                              "whole_attempt_events": False, "complete_bundle": False}
        result["display"] = {"matched": len(deaths), "returned": len(deaths), "truncated": False}
        return result
    if args.death is not None and args.death > len(deaths):
        raise DataError("Death ordinal does not identify a candidate death.")
    selected = deaths[(args.death or 1) - 1]
    if guarded and selected["timestamp"] != args.expected_death_timestamp:
        raise DataError("Selected death timestamp does not match the expected timestamp.")
    requested = [selected["timestamp"] - args.before_ms, selected["timestamp"] + args.after_ms]
    actual = [max(fight["start_ms"], requested[0]), min(fight["end_ms"], requested[1])]
    events, pagination = pages(client, result["identity"], args.fight_id, *actual, "")
    events = [event for event in events if args.actor_id in (event.get("sourceID"), event.get("targetID"))]
    if not any(event["type"] == "death" and event["timestamp"] == selected["timestamp"]
               and event.get("targetID") == args.actor_id and event.get("feign") is not True
               for event in events):
        raise DataError("Selected death is missing from the retrieved event window.")
    check_revision(client, code, result["identity"]["report_revision"])
    referenced = {args.actor_id}
    for event in events:
        referenced.update(event.get(key) for key in ("sourceID", "targetID") if event.get(key) is not None)
    result["actors"] = [a for a in result["actors"] if a["actor_id"] in referenced]
    result["warnings"] = ["Some event actor IDs have no master-data identity."] if referenced - {
        a["actor_id"] for a in result["actors"]} else []
    result["death"] = selected
    result["events"] = events[:args.limit]
    result["coverage"] = {"scope": "participant_source_or_target", "requested_window_ms": requested,
                          "actual_window_ms": actual, "upstream_window_scope": "all_actors",
                          "actor_filter": "local sourceID or targetID", "death_search_scope": "all_actor_deaths",
                          "death_search_window_ms": [fight["start_ms"], fight["end_ms"]],
                          "death_pagination": death_pagination, "event_pagination": pagination,
                          "query_complete": True, "revision_consistent": True,
                          "whole_attempt_events": False, "complete_bundle": False}
    result["display"] = {"matched": len(events), "returned": len(result["events"]),
                         "truncated": len(events) > args.limit}
    return result


def events_report(client, code, args):
    result = index(client, code)
    if (args.expected_revision is not None
            and result["identity"]["report_revision"] != args.expected_revision):
        raise DataError("Expected Report Revision does not match the retrieved report.")
    fight = next((f for f in result["attempts"] if f["fight_id"] == args.fight_id), None)
    if fight is None:
        raise DataError("Fight ID does not identify a supported Boss Attempt.")
    requested = [args.start_ms, args.end_ms]
    actual = [max(fight["start_ms"], requested[0]), min(fight["end_ms"], requested[1])]
    if actual[0] > actual[1]:
        raise DataError("Requested range does not overlap the Boss Attempt.")
    result.pop("attempts")
    result["identity"]["fight_id"] = args.fight_id
    result["attempt"] = fight
    result["source"]["url"] += f"#fight={args.fight_id}"
    actor_role = args.actor_role or ("either" if args.actor_id is not None else None)
    if args.actor_id is not None and not any(
            participant["actor_id"] == args.actor_id for participant in fight["participants"]):
        raise DataError("Actor ID is not a participant of this Boss Attempt.")
    filters = []
    if args.event_type is not None:
        filters.append(f"type = '{args.event_type}'")
    if args.spell_id is not None:
        filters.append(f"ability.id = {args.spell_id}")
    expression = " AND ".join(filters)
    upstream_range = [math.floor(actual[0]), math.ceil(actual[1])]
    events, pagination = pages(client, result["identity"], args.fight_id, *upstream_range,
                               expression, args.event_type)
    if args.spell_id is not None and any(
            event.get("abilityGameID") != args.spell_id for event in events):
        raise DataError("Spell filter did not match returned ability game IDs.")
    events = [event for event in events if actual[0] <= event["timestamp"] <= actual[1]]
    if args.actor_id is not None:
        if actor_role == "source":
            events = [event for event in events if event.get("sourceID") == args.actor_id]
        elif actor_role == "target":
            events = [event for event in events if event.get("targetID") == args.actor_id]
        else:
            events = [event for event in events if args.actor_id in (
                event.get("sourceID"), event.get("targetID"))]
    check_revision(client, code, result["identity"]["report_revision"])
    result["events"] = events[:args.limit]
    referenced = {args.actor_id} if args.actor_id is not None else set()
    for event in result["events"]:
        referenced.update(event.get(key) for key in ("sourceID", "targetID")
                          if event.get(key) is not None)
    result["actors"] = [actor for actor in result["actors"] if actor["actor_id"] in referenced]
    result["warnings"] = (["Some event actor IDs have no master-data identity."]
                          if referenced - {actor["actor_id"] for actor in result["actors"]} else [])
    result["query"] = {
        "requested_range_ms": requested,
        "actual_range_ms": actual,
        "filters": {"spell_id": args.spell_id, "event_type": args.event_type,
                    "actor_id": args.actor_id, "actor_role": actor_role},
    }
    result["coverage"] = {
        "scope": "bounded_attempt_events", "upstream_range_ms": upstream_range,
        "upstream_filter": expression or None, "local_filter": "report-relative timestamp",
        "event_pagination": pagination, "query_complete": True,
        "revision_consistent": True,
        "whole_attempt_events": (actual == [fight["start_ms"], fight["end_ms"]]
                                 and not any((args.spell_id, args.event_type, args.actor_id))),
        "complete_bundle": False,
    }
    if args.actor_id is not None:
        result["coverage"]["actor_filter"] = (
            "local sourceID or targetID" if actor_role == "either" else f"local {actor_role}ID")
    result["display"] = {"matched": len(events), "returned": len(result["events"]),
                         "truncated": len(events) > args.limit}
    return result


def deaths_report(client, code, args):
    result = index(client, code)
    fight = next((f for f in result["attempts"] if f["fight_id"] == args.fight_id), None)
    if fight is None:
        raise DataError("Fight ID does not identify a supported Boss Attempt.")
    result.pop("attempts")
    result["identity"]["fight_id"] = args.fight_id
    result["attempt"] = fight
    result["source"]["url"] += f"#fight={args.fight_id}"
    participant_ids = {participant["actor_id"] for participant in fight["participants"]}
    events, death_pagination = pages(client, result["identity"], args.fight_id, fight["start_ms"],
                                     fight["end_ms"], "type = 'death'", "death")
    deaths, classification = classify_deaths(events, participant_ids)
    check_revision(client, code, result["identity"]["report_revision"])
    result["actors"] = [actor for actor in result["actors"] if actor["actor_id"] in participant_ids]
    result["death_classification"] = classification
    result["deaths"] = death_records(deaths)
    result["status"] = "ok" if deaths else "no_death"
    result["coverage"] = {"scope": "participant_deaths", "death_pagination": death_pagination,
                          "death_search_scope": "all_actor_deaths",
                          "actor_filter": "local targetID against attempt participants",
                          "death_search_window_ms": [fight["start_ms"], fight["end_ms"]],
                          "query_complete": True, "revision_consistent": True,
                          "whole_attempt_events": False, "complete_bundle": False}
    result["display"] = {"matched": len(deaths), "returned": min(len(deaths), args.limit),
                         "truncated": len(deaths) > args.limit}
    result["deaths"] = result["deaths"][:args.limit]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index").add_argument("report")
    events = commands.add_parser("events")
    events.add_argument("report")
    events.add_argument("--fight-id", type=int, required=True)
    events.add_argument("--start-ms", type=float, required=True)
    events.add_argument("--end-ms", type=float, required=True)
    events.add_argument("--spell-id", type=int)
    events.add_argument("--event-type", choices=sorted(EVENT_TYPES))
    events.add_argument("--actor-id", type=int)
    events.add_argument("--actor-role", choices=("source", "target", "either"))
    events.add_argument("--expected-revision", type=int)
    events.add_argument("--limit", type=int, default=100)
    deaths = commands.add_parser("deaths")
    deaths.add_argument("report")
    deaths.add_argument("--fight-id", type=int, required=True)
    deaths.add_argument("--limit", type=int, default=100)
    window = commands.add_parser("death-window")
    window.add_argument("report")
    window.add_argument("--fight-id", type=int, required=True)
    window.add_argument("--actor-id", type=int, required=True)
    window.add_argument("--death", type=int)
    window.add_argument("--before-ms", type=int, default=10000)
    window.add_argument("--after-ms", type=int, default=5000)
    window.add_argument("--limit", type=int, default=100)
    window.add_argument("--expected-revision", type=int)
    window.add_argument("--expected-death-timestamp", type=float)
    args = parser.parse_args(argv)
    try:
        code = report_code(args.report)
        if args.command == "events":
            if (args.fight_id <= 0 or args.limit < 0 or not finite_number(args.start_ms)
                    or not finite_number(args.end_ms) or args.start_ms < 0
                    or args.start_ms >= args.end_ms or (args.spell_id is not None and args.spell_id <= 0)
                    or (args.actor_id is not None and args.actor_id <= 0)
                    or (args.expected_revision is not None and args.expected_revision <= 0)
                    or (args.actor_role is not None and args.actor_id is None)):
                raise DataError("Fight ID must be positive; range must be finite, nonnegative and increasing; limit must be nonnegative.")
        elif args.command == "deaths":
            if args.fight_id <= 0 or args.limit < 0:
                raise DataError("Fight ID must be positive and limit must be nonnegative.")
        elif args.command == "death-window":
            if (args.fight_id <= 0 or args.actor_id <= 0
                    or (args.death is not None and args.death <= 0)
                    or min(args.before_ms, args.after_ms, args.limit) < 0):
                raise DataError("IDs/death ordinal must be positive; window sizes and limit must be nonnegative.")
            if (args.expected_revision is None) != (args.expected_death_timestamp is None):
                raise DataError("Expected Revision and death timestamp must be supplied together.")
            if args.expected_revision is not None and (
                    args.expected_revision <= 0 or not finite_number(args.expected_death_timestamp)
                    or args.expected_death_timestamp < 0):
                raise DataError("Expected Revision must be positive and death timestamp finite and nonnegative.")
            if (args.expected_revision is not None and args.death is None):
                raise DataError("An explicit death ordinal is required with expected identity guards.")
        client = Client()
        if args.command == "index":
            result = index(client, code)
        elif args.command == "events":
            result = events_report(client, code, args)
        elif args.command == "deaths":
            result = deaths_report(client, code, args)
        else:
            result = death_window(client, code, args)
        output = json.dumps(result, ensure_ascii=False, allow_nan=False)
    except DataError as exc:
        print(json.dumps({"status": "error", "error": str(exc), "coverage": {"query_complete": False}}))
        return 1
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        print(json.dumps({"status": "error", "error": "Malformed WCL data or invalid selection.",
                          "coverage": {"query_complete": False}}))
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
