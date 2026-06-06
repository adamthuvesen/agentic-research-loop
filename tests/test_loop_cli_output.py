from __future__ import annotations


from agentic_research_loop.run_ui import format_elapsed, print_run_footer


def test_format_elapsed_handles_short_and_long_durations() -> None:
    assert format_elapsed(0) == "0s"
    assert format_elapsed(59) == "59s"
    assert format_elapsed(61) == "1m 1s"
    assert format_elapsed(3661) == "1h 1m"


def test_print_run_footer_shows_cycle_count_and_last_result(capsys) -> None:
    summaries = [{"result": "progress"}, {"result": "complete"}]
    print_run_footer(summaries)
    captured = capsys.readouterr()
    assert "2" in captured.out
    assert "complete" in captured.out


def test_print_run_footer_no_cycles(capsys) -> None:
    print_run_footer([])
    captured = capsys.readouterr()
    assert "0" in captured.out
    # no last-result separator when list is empty
    assert "·" not in captured.out
