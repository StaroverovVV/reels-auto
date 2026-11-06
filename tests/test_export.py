import tempfile
import unittest
from pathlib import Path
from openfilm_export import export


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'fixture.mp4'
        self.source.write_bytes(b'synthetic placeholder')
        self.plan = {'video': str(self.source), 'start': 0.3, 'end': 2.3,
                     'fit': 'cover', 'captions_reviewed': True,
                     'captions': [{'start': .2, 'end': 1.2, 'text': 'Тестовые титры'}]}

    def test_vertical_export_with_timed_vtt(self):
        dest = export(self.plan, self.root / 'film')
        doc = (dest / 'film.html').read_text()
        self.assertIn('width=1080, height=1920', doc)
        self.assertIn('#t=0.300,2.300', doc)
        self.assertIn('object-fit:cover', doc)
        cues = (dest / 'assets/source.vtt').read_text()
        self.assertIn('00:00:00.500 --> 00:00:01.500', cues)
        self.assertIn('Тестовые титры', cues)

    def test_review_gate(self):
        self.plan['captions_reviewed'] = False
        with self.assertRaisesRegex(ValueError, 'reviewed'):
            export(self.plan, self.root / 'film')

    def test_never_overwrite(self):
        dest = export(self.plan, self.root / 'film')
        (dest / 'film.html').write_text('MANUAL EDIT')
        with self.assertRaises(FileExistsError):
            export(self.plan, dest)
        self.assertEqual((dest / 'film.html').read_text(), 'MANUAL EDIT')

    def test_bad_timings(self):
        for bad in [float('inf'), float('nan'), -1, 3]:
            with self.assertRaises(ValueError):
                export({**self.plan, 'start': bad}, self.root / 'film')
        self.plan['captions'][0]['end'] = 10
        with self.assertRaises(ValueError):
            export(self.plan, self.root / 'film')

    def test_voice_separate_from_video(self):
        voice = self.root / 'voice.wav'
        voice.write_bytes(b'fixture')
        self.plan['voice'] = str(voice)
        dest = export(self.plan, self.root / 'film')
        html = (dest / 'film.html').read_text()
        self.assertIn('volume="0"', html)
        self.assertIn('<audio id="voice"', html)
        self.assertTrue((dest / 'assets/voice.vtt').is_file())
        self.assertFalse((dest / 'assets/source.vtt').exists())

    def test_original_untouched(self):
        dest = export(self.plan, self.root / 'film')
        self.assertEqual(self.source.read_bytes(), (dest / 'assets/source.mp4').read_bytes())


if __name__ == '__main__':
    unittest.main()
