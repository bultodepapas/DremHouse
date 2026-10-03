"""File-save bursts and transient failures never select a partial revision."""

import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from dreamhouse.coordination.watch import build_fresh_process, watch_sources


class WatchTests(unittest.TestCase):
    def test_each_rebuild_loads_code_in_new_interpreter_and_propagates_failure(self):
        with patch("dreamhouse.coordination.watch.subprocess.run") as run:
            run.return_value = CompletedProcess([], 0, '{"path":"complete"}', "")
            self.assertEqual(
                build_fresh_process(Path("study.json"), Path(".build/review")), {"path": "complete"}
            )
            build_fresh_process(Path("study.json"), Path(".build/review"), visuals=True)
            self.assertEqual(run.call_count, 2)
            args, kwargs = run.call_args
            self.assertEqual(args[0][-1], "yes")
            self.assertNotIn("shell", kwargs)
            run.return_value = CompletedProcess([], 1, "", "new loader failed")
            with self.assertRaisesRegex(RuntimeError, "new loader failed"):
                build_fresh_process(Path("study.json"), Path(".build/review"))

    def test_bursts_partial_json_and_failed_build_recover_on_next_edit(self):
        samples = [
            "old",
            "edit1",
            ValueError("partial JSON"),
            "edit2",
            "edit2",
            "edit2",
            "edit3",
            "edit3",
            "edit3",
        ]
        built = []
        messages = []

        class Stop:
            position = 0

            def is_set(self):
                return self.position >= len(samples)

            def wait(self, seconds):
                self.position += 1

        stop = Stop()

        def fingerprint():
            value = samples[stop.position]
            if isinstance(value, Exception):
                raise value
            return value

        def build():
            value = samples[stop.position]
            built.append(value)
            if value == "edit2":
                raise ValueError("synthetic renderer failure")
            return {"path": "complete"}

        watch_sources(
            Path("study.json"),
            build,
            stop=stop,
            interval=1,
            debounce=1,
            fingerprint=fingerprint,
            clock=lambda: float(stop.position),
            notify=messages.append,
        )
        self.assertEqual(built, ["edit2", "edit3"])
        self.assertTrue(any("partial JSON" in m for m in messages))
        self.assertTrue(any("Review unchanged" in m for m in messages))
        self.assertEqual(messages[-1], "Built review: complete/index.html")

    def test_invalid_timing_rejected_before_work(self):
        for interval, debounce in ((0, 1), (1, -1), (float("inf"), 1)):
            with self.subTest(interval=interval, debounce=debounce), self.assertRaises(ValueError):
                watch_sources(Path("unused"), dict, interval=interval, debounce=debounce)
