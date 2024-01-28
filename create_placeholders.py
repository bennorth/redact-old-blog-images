#!/usr/bin/env python
# coding: utf-8

import json
import math
import os
import sys
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

hosting_home = os.getenv("HOSTING_HOME")
site_name = os.getenv("SITE_NAME")

if hosting_home is None or site_name is None:
    print(
        "please set HOSTING_HOME and SITE_NAME",
        file=sys.stderr
    )
    sys.exit(1)

base_path = Path(hosting_home) / site_name / "wp-content/uploads"

font_dir = Path("~/.fonts/NerdFont").expanduser()
font_path = str(font_dir / "IosevkaNerdFont-Medium.ttf")


########################################################################

def argmin(xs):
    min_idx = 0
    min_val = xs[0]
    for idx in range(1, len(xs)):
        val = xs[idx]
        if val < min_val:
            min_idx = idx
            min_val = val
    return min_idx


########################################################################

text_lines_candidates = [
    ["old image removed in line with data protection policy"],
    ["old image removed in line", "with data protection policy"],
    ["old image removed", "in line with data", "protection policy"],
    ["old image removed", "in line with", "data protection", "policy"],
    ["old image", "removed in", "line with", "data", "protection", "policy"],
]

text_candidates = ["\n".join(lines) for lines in text_lines_candidates]


########################################################################

class TextMeasure:
    def __init__(self):
        self.img = Image.new("RGBA", (100, 100))
        self.draw = ImageDraw.Draw(self.img)
        self.candidate_aspects = [
            self.aspect(text, 72)  # Big; reduce pixel grid effects
            for text in text_candidates
        ]

    def measure(self, text, font_size):
        font = ImageFont.truetype(font_path, font_size)
        bbox = self.draw.textbbox(
            (50, 50),
            text,
            align="center",
            anchor="mm",
            font=font
        )
        shape = (float(bbox[2] - bbox[0]), float(bbox[3] - bbox[1]))
        return shape

    def aspect(self, text, font_size):
        shape = self.measure(text, font_size)
        return shape[0] / shape[1]

    def best_text(self, aspect):
        abs_log_ratios = [
            abs(math.log(candidate_aspect / aspect))
            for candidate_aspect in self.candidate_aspects
        ]
        min_idx = argmin(abs_log_ratios)
        return text_candidates[min_idx]

    def image(self, img_shape):
        img_aspect = img_shape[0] / img_shape[1]
        best_text = self.best_text(img_aspect)
        aa_scale = 3
        aa_shape = (aa_scale * img_shape[0], aa_scale * img_shape[1])
        aa_img = Image.new("RGBA", aa_shape, color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(aa_img)
        draw.rounded_rectangle(
            (
                aa_scale,
                aa_scale,
                aa_shape[0] - aa_scale - 1,
                aa_shape[1] - aa_scale - 1
            ),
            radius=aa_scale * 8,
            fill="#71caf2"
        )
        font_size = aa_scale * 18
        text_shape = self.measure(best_text, font_size)
        wd_fraction = text_shape[0] / aa_shape[0]
        ht_fraction = text_shape[1] / aa_shape[1]
        max_fraction = 0.8
        font_rescale = min(1, max_fraction / max(wd_fraction, ht_fraction))
        if font_rescale < 1:
            font_size = math.floor(font_rescale * font_size)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(
            (aa_shape[0] // 2, aa_shape[1] // 2),
            best_text,
            (0, 0, 0),
            align="center",
            anchor="mm",
            font=font
        )
        img = aa_img.resize(img_shape, Image.Resampling.LANCZOS)
        return img

text_measure = TextMeasure()


########################################################################

image_data = json.load(open("results.json"))

for record in image_data:
    record["relpath"] = str(Path(record["fullpath"]).relative_to(base_path))

out_dir = Path("images-out")
os.makedirs(out_dir / "placeholders-for-removed", exist_ok=True)

sizes_written = set()
for record in image_data:
    img_wd = record["x"]
    img_ht = record["y"]
    img_size = (img_wd, img_ht)
    basename = f"{img_wd:05d}-{img_ht:05d}.png"
    placeholder_path = f"placeholders-for-removed/{basename}"
    if img_size not in sizes_written:
        img = text_measure.image(img_size)
        out_path = out_dir / placeholder_path
        img.save(str(out_path))
        sizes_written.add(img_size)
    n_dirs_up = len(Path(record["relpath"]).parts) - 1
    rel_prefix = "../" * n_dirs_up
    link_tgt_path = rel_prefix + placeholder_path
    link_path = out_dir / record["relpath"]
    os.makedirs(Path(link_path).parent, exist_ok=True)
    os.symlink(link_tgt_path, link_path)
