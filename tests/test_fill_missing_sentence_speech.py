import unittest

from addon.repair_logic import (
    SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED,
    SENTENCE_AUDIO_STATUS_FILLED,
    SENTENCE_AUDIO_STATUS_PENDING,
    SENTENCE_AUDIO_STATUS_UNAVAILABLE_UPSTREAM,
    apply_sentence_audio_status_to_sentences,
    build_sentence_audio_download_plan,
    collect_sentence_audio_repair_reasons,
    finalize_sentence_audio_slot_status,
)


class FillMissingSentenceSpeechTests(unittest.TestCase):
    def test_collect_sentence_audio_repair_reasons_marks_empty_speech(self):
        reasons = collect_sentence_audio_repair_reasons(
            ["A sentence", "", "Another sentence"],
            ["", "", "[sound:MG-test_s2.mp3]"],
            "/tmp/media",
            lambda _field_value, _media_dir: False,
        )
        self.assertIn("sentence_speech0:empty", reasons)
        self.assertNotIn("sentence_speech1:empty", reasons)

    def test_collect_sentence_audio_repair_reasons_marks_missing_file(self):
        reasons = collect_sentence_audio_repair_reasons(
            ["A sentence"],
            ["[sound:MG-test_s0.mp3]"],
            "/tmp/media",
            lambda field_value, _media_dir: field_value == "[sound:MG-test_s0.mp3]",
        )
        self.assertEqual(reasons, ["sentence_speech0:file-missing"])

    def test_build_sentence_audio_download_plan(self):
        tasks, slot_status, slot_filename = build_sentence_audio_download_plan(
            "square with",
            [
                ("s0", "e0", "http://audio0"),
                ("s1", "e1", ""),
            ],
        )
        self.assertEqual(tasks, [("MG-square with_s0.mp3", "http://audio0")])
        self.assertEqual(slot_status[0], SENTENCE_AUDIO_STATUS_PENDING)
        self.assertEqual(slot_status[1], SENTENCE_AUDIO_STATUS_UNAVAILABLE_UPSTREAM)
        self.assertEqual(slot_filename[0], "MG-square with_s0.mp3")

    def test_finalize_sentence_audio_slot_status(self):
        slot_status = {0: SENTENCE_AUDIO_STATUS_PENDING, 1: SENTENCE_AUDIO_STATUS_PENDING}
        slot_filename = {0: "ok.mp3", 1: "fail.mp3"}

        finalized = finalize_sentence_audio_slot_status(
            slot_status,
            slot_filename,
            "/tmp/media",
            {"ok.mp3": "filled", "fail.mp3": "download-failed"},
            file_exists=lambda path: path.endswith("ok.mp3"),
        )

        self.assertEqual(finalized[0], SENTENCE_AUDIO_STATUS_FILLED)
        self.assertEqual(finalized[1], SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED)

    def test_apply_sentence_audio_status_to_sentences(self):
        sentences = [
            ("s0", "e0", "http://audio0"),
            ("s1", "e1", "http://audio1"),
        ]
        patched = apply_sentence_audio_status_to_sentences(
            sentences,
            {0: SENTENCE_AUDIO_STATUS_FILLED, 1: SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED},
        )
        self.assertEqual(patched[0][2], "http://audio0")
        self.assertEqual(patched[1][2], "")


if __name__ == '__main__':
    unittest.main()
