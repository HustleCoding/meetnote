from meetnote.detect import active_meeting_apps, is_meeting_active

DETECT = ["zoom.us", "Microsoft Teams", "Slack"]


def test_detects_running_meeting_app():
    procs = ["Finder", "zoom.us", "Google Chrome"]
    assert active_meeting_apps(DETECT, procs) == ["zoom.us"]
    assert is_meeting_active(DETECT, procs) is True


def test_matching_is_case_insensitive():
    procs = ["ZOOM.US Helper"]
    assert active_meeting_apps(DETECT, procs) == ["zoom.us"]


def test_no_meeting_app_running():
    procs = ["Finder", "Google Chrome", "Notes"]
    assert active_meeting_apps(DETECT, procs) == []
    assert is_meeting_active(DETECT, procs) is False


def test_multiple_meeting_apps():
    procs = ["zoom.us", "Slack Helper"]
    assert set(active_meeting_apps(DETECT, procs)) == {"zoom.us", "Slack"}
