"""Behavioral tests; all generated fonts and figures stay in temporary folders."""

from pathlib import Path
import hashlib
import tempfile
import unittest
import xml.etree.ElementTree as ET

from fontTools.ttLib import TTCollection, TTFont
from matplotlib import font_manager, ft2font, rc_context
from matplotlib.artist import Artist
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text
import numpy as np
from PIL import Image

from research_charts import ChartTheme, label_bars, label_points, stacked_bars


class ChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory()
        cls.root = Path(cls.scratch.name)
        try:
            cls.theme = ChartTheme(cls.root)
        except ValueError as exc:
            cls.scratch.cleanup()
            raise unittest.SkipTest(f"Verified Simplified Chinese integration font unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def figure(self):
        fig = self.theme.figure("合成测试：收入与回报", "单位：示例值；不含真实公司数据")
        ax = self.theme.axes(fig.add_subplot())
        ax.plot([0, 1, 2], [1, 2, 1], label="测试序列")
        ax.set_xticks([0, 1, 2], ["第一期", "第二期", "第三期"])
        return fig, ax

    def test_selects_sc_face_not_first_collection_face(self):
        with tempfile.TemporaryDirectory() as folder:
            collection = TTCollection()
            collection.fonts = [
                TTFont(font_manager.findfont("DejaVu Sans")),
                TTFont(self.theme.font_path),
            ]
            target = Path(folder) / "mixed-collection.ttc"
            try:
                collection.save(target)
            finally:
                collection.close()
            theme = ChartTheme(folder, font_path=target)
            self.assertEqual(theme.font_identity["source_face_index"], 1)
            self.assertEqual(theme.font_identity["postscript_name"],
                             self.theme.font_identity["postscript_name"])
            self.assertEqual(ft2font.FT2Font(str(theme.font_path)).postscript_name,
                             theme.font_identity["postscript_name"])
            self.assertEqual(theme.font_path.parent, Path(folder) / "font-cache")

    def test_rejects_generic_font_even_with_chinese_fallback_available(self):
        with self.assertRaisesRegex(ValueError, "No verified Simplified Chinese"):
            ChartTheme(self.root, font_path=font_manager.findfont("DejaVu Sans"))

    def test_custom_sc_face_requires_bound_evidence_and_retains_export_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / self.theme.font_path.name
            font = TTFont(self.theme.font_path, recalcTimestamp=False)
            name = "ResearchTestSC-Regular"
            try:
                for record in font["name"].names:
                    if record.nameID == 6:
                        record.string = name.encode(record.getEncoding())
                if "CFF " in font:
                    font["CFF "].cff.fontNames = [name]
                font.save(path)
            finally:
                font.close()
            evidence = {
                "postscript_name": name,
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "verification_note": "Test fixture: names changed on verified SC face; glyphs unchanged.",
            }
            with self.assertRaisesRegex(ValueError, "No verified Simplified Chinese"):
                ChartTheme(folder, font_path=path)
            theme = ChartTheme(folder, font_path=path, font_verification=evidence)
            self.assertEqual(ft2font.FT2Font(str(theme.font_path)).postscript_name, name)
            # Caller edits cannot alter the recorded evidence after selection.
            expected = dict(evidence)
            evidence["verification_note"] = "changed after selection"
            fig = theme.figure("简体中文：收入与回报")
            audit = theme.export(fig, Path(folder) / "custom")
            self.assertEqual(audit["font"]["verification"], expected)
            self.assertEqual(audit["font"]["postscript_name"], name)
            self.assertEqual(audit["glyphs"]["status"], "pass")
            self.assertEqual(audit["visual_review"], "required")
            fig.text(.5, .5, "\U0010ffff")
            with self.assertRaisesRegex(ValueError, "Missing glyphs.*U\\+10FFFF"):
                theme.export(fig, Path(folder) / "custom-missing")
            self.assertFalse((Path(folder) / "custom-missing.png").exists())
            for changes, error in [
                ({"source_sha256": "0" * 64}, "source_sha256 mismatch"),
                ({"postscript_name": "OtherSC-Regular"}, "postscript_name mismatch"),
                ({"verification_note": " "}, "independent SC verification_note"),
            ]:
                with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, error):
                    ChartTheme(folder, font_path=path, font_verification={**expected, **changes})
            with self.assertRaisesRegex(ValueError, "font_verification requires font_path"):
                ChartTheme(folder, font_verification=expected)

    def test_custom_verification_cannot_replace_missing_chinese_glyphs(self):
        path = Path(font_manager.findfont("DejaVu Sans"))
        evidence = {
            "postscript_name": ft2font.FT2Font(str(path)).postscript_name,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "verification_note": "Deliberately invalid evidence: glyph checks must still reject this.",
        }
        with self.assertRaisesRegex(ValueError, "required SC glyphs missing"):
            ChartTheme(self.root, font_path=path, font_verification=evidence)

    def test_missing_glyph_fails_before_writing(self):
        fig, ax = self.figure()
        ax.text(.5, .5, "缺失字符\U0010ffff", transform=ax.transAxes)
        target = self.root / "missing.png"
        with self.assertRaisesRegex(ValueError, "Missing glyphs.*U\\+10FFFF"):
            self.theme.export(fig, target)
        self.assertFalse(target.exists())

    def test_native_chinese_categories_inherit_verified_font_on_first_draw(self):
        fig = self.theme.figure("原生中文分类柱图")
        ax = self.theme.axes(fig.add_subplot())
        categories = ["第一期", "第二期", "第三期"]
        ax.bar(categories, [1, 3, 2])
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "categories.png"
            audit = self.theme.export(fig, target)
            self.assertTrue(target.exists())
            self.assertEqual(audit["glyphs"]["status"], "pass")
            self.assertEqual([text.get_text() for text in ax.get_xticklabels()], categories)
            for text in ax.get_xticklabels():
                self.assertEqual(text.get_fontproperties().get_file(), str(self.theme.font_path))

    def test_canvas_clipping_fails_before_writing(self):
        fig, _ = self.figure()
        fig.text(1.02, .5, "超出画布", fontproperties=self.theme._font(10))
        target = self.root / "clipped.png"
        with self.assertRaisesRegex(ValueError, "Text clips the canvas"):
            self.theme.export(fig, target)
        self.assertFalse(target.exists())

    def test_signed_stacks_and_incomplete_periods(self):
        fig = self.theme.figure("正负堆叠与缺失")
        ax = self.theme.axes(fig.add_subplot())
        stack = stacked_bars(ax, [0, 1, 2, 3], {
            "甲": [3, -3, np.nan, 0], "乙": [-2, -2, 4, 0], "丙": [4, 1, 0, 0],
        })
        np.testing.assert_array_equal(stack["complete_mask"], [True, True, False, True])
        np.testing.assert_array_equal(stack["missing_mask"], [False, False, True, False])
        bars = stack["containers"]
        self.assertEqual(bars["乙"][0].get_y(), 0)
        self.assertEqual(bars["乙"][1].get_y(), -3)
        self.assertEqual(bars["丙"][0].get_y(), 3)
        self.assertEqual(bars["丙"][1].get_y(), 0)
        for container in bars.values():
            self.assertTrue(np.isnan(container[2].get_height()))
            self.assertEqual(container[3].get_height(), 0)
        self.assertEqual([bar.get_height() for bar in bars["乙"][:2]], [-2, -2])

    def test_labels_keep_missing_values_blank(self):
        fig = self.theme.figure("标注测试")
        ax = self.theme.axes(fig.add_subplot())
        bars = ax.bar([0, 1, 2], [2, -1, np.nan])
        bar_labels = label_bars(ax, bars)
        self.assertEqual([label.get_text() for label in bar_labels], ["2.0", "-1.0", ""])
        point_labels = label_points(ax, [0, 1, 2], [2, np.nan, -1],
                                    offsets={2: (2, -10)})
        self.assertEqual(len(point_labels), 2)
        self.assertEqual(point_labels[1].xyann, (2, -10))

    def test_png_default_and_every_text_is_pinned(self):
        fig, ax = self.figure()
        ax.set_ylabel("金额")
        ax.text(.5, .5, "$10 / $20", transform=ax.transAxes)
        ax.annotate("注释", (1, 2), xytext=(8, -18), textcoords="offset points")
        ax.legend(loc="upper left")
        table = ax.table(cellText=[["合成", "12.5"]], rowLabels=["行标签"],
                         colLabels=["项目", "数值"], bbox=[.45, .05, .45, .1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        self.theme.footer(fig, "来源：合成数据\n口径：仅用于验证")
        with tempfile.TemporaryDirectory() as folder:
            with rc_context({"savefig.bbox": "tight"}):
                audit = self.theme.export(fig, Path(folder) / "chart")
            self.assertEqual({p.name for p in Path(folder).iterdir()}, {"chart.png"})
            self.assertEqual(audit["visual_review"], "required")
            self.assertEqual(audit["glyphs"]["status"], "pass")
            self.assertEqual(len(audit["outputs"]["png"]["sha256"]), 64)
            with Image.open(Path(folder) / "chart.png") as im:
                self.assertEqual(im.width, round(fig.get_figwidth() * fig.dpi))
            for text in fig.findobj(Text):
                if text.get_visible() and text.get_text():
                    self.assertEqual(text.get_fontproperties().get_file(), str(self.theme.font_path))
                    self.assertFalse(text.get_parse_math())
            for cell in table.get_celld().values():
                self.assertEqual(cell.get_text().get_fontproperties().get_file(),
                                 str(self.theme.font_path))

    def test_refuses_accidental_replacement_and_allows_explicit_replacement(self):
        fig, _ = self.figure()
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "chart.png"
            target.write_bytes(b"original content")
            with self.assertRaises(FileExistsError):
                self.theme.export(fig, target)
            self.assertEqual(target.read_bytes(), b"original content")
            self.theme.export(fig, target, replace=True)
            self.assertEqual(target.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_table_cell_missing_glyph_and_canvas_clipping_fail(self):
        fig, ax = self.figure()
        table = ax.table(cellText=[["正常"]], rowLabels=["缺字\U0010ffff"],
                         bbox=[.4, .2, .3, .15])
        target = self.root / "bad-table.png"
        with self.assertRaisesRegex(ValueError, "Missing glyphs.*U\\+10FFFF"):
            self.theme.export(fig, target)
        self.assertFalse(target.exists())
        table.remove()
        table = ax.table(cellText=[["正常"]], rowLabels=["中文行标签"],
                         bbox=[1.1, .2, .5, .15])
        with self.assertRaisesRegex(ValueError, "Text clips the canvas"):
            self.theme.export(fig, target)
        self.assertFalse(target.exists())
        table.remove()
        ax.table(cellText=[["正常"]], rowLabels=["中文行标签"], bbox=[.4, .2, .3, .15])
        self.theme.export(fig, target)
        self.assertTrue(target.exists())

    def test_untraversed_missing_glyph_render_warning_fails(self):
        fig, _ = self.figure()

        class OnDemandText(Artist):
            def draw(self, renderer):
                text = Text(.5, .5, "中文", transform=fig.transFigure,
                            fontproperties=FontProperties(fname=font_manager.findfont("DejaVu Sans")))
                text.set_figure(fig)
                text.draw(renderer)

        fig.add_artist(OnDemandText())
        target = self.root / "hidden-fallback.png"
        with self.assertRaisesRegex(ValueError, "Renderer font/glyph check failed"):
            self.theme.export(fig, target)
        self.assertFalse(target.exists())

    def test_optional_svg_uses_outlines_without_extra_png(self):
        fig, _ = self.figure()
        with tempfile.TemporaryDirectory() as folder:
            audit = self.theme.export(fig, Path(folder) / "chart", formats=("svg",))
            self.assertEqual({p.name for p in Path(folder).iterdir()}, {"chart.svg"})
            root = ET.parse(Path(folder) / "chart.svg").getroot()
            self.assertFalse(root.findall(".//{http://www.w3.org/2000/svg}text"))
            self.assertTrue(root.findall(".//{http://www.w3.org/2000/svg}path"))
            self.assertEqual(set(audit["outputs"]), {"svg"})

    def test_optional_pdf_embeds_selected_font(self):
        fig, _ = self.figure()
        with tempfile.TemporaryDirectory() as folder:
            self.theme.export(fig, Path(folder) / "chart", formats=("pdf",))
            content = (Path(folder) / "chart.pdf").read_bytes()
            self.assertIn(b"/FontFile2", content)
            self.assertNotIn(b"/Subtype /Type3", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
