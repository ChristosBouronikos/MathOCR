"""Region-merging tests for MathOCR by Bouronikos Christos <chrisbouronikos@gmail.com>.

Support the project at https://paypal.me/christosbouronikos. These tests
document the fix for the old bug where a tall fraction or a wide equation was
recognized in fragments.
"""

from backend.geometry import Box, merge_fragmented_boxes, padded_crop_box, plan_regions


def test_fraction_split_into_numerator_and_denominator_is_merged() -> None:
    numerator = Box(100, 100, 500, 160)
    denominator = Box(120, 175, 480, 235)  # small gap: the fraction bar region
    merged = merge_fragmented_boxes([numerator, denominator])
    assert merged == [Box(100, 100, 500, 235)]


def test_equation_cut_at_an_operator_is_merged() -> None:
    left_half = Box(50, 200, 400, 260)
    right_half = Box(430, 205, 700, 258)  # gap of 30px ≈ half the glyph height
    merged = merge_fragmented_boxes([left_half, right_half])
    assert merged == [Box(50, 200, 700, 260)]


def test_chain_of_three_fragments_collapses_into_one() -> None:
    top = Box(100, 100, 500, 150)
    middle = Box(100, 160, 500, 210)
    bottom = Box(100, 220, 500, 270)
    assert merge_fragmented_boxes([bottom, top, middle]) == [Box(100, 100, 500, 270)]


def test_distinct_display_equations_on_a_page_stay_separate() -> None:
    first_line = Box(100, 100, 600, 160)
    second_line = Box(100, 240, 600, 300)  # a full text line apart
    merged = merge_fragmented_boxes([first_line, second_line])
    assert len(merged) == 2


def test_side_by_side_column_equations_stay_separate() -> None:
    left_column = Box(50, 100, 300, 160)
    right_column = Box(500, 100, 750, 160)  # far apart horizontally
    assert len(merge_fragmented_boxes([left_column, right_column])) == 2


def test_plan_regions_treats_dominant_detection_as_single_formula() -> None:
    # A cropped complicated equation: detection covers most of the image.
    assert plan_regions(800, 400, [Box(40, 30, 770, 370)]) is None


def test_plan_regions_treats_fragmented_crop_as_single_formula() -> None:
    # The old failure: MFD reports a big fraction as stacked fragments.
    fragments = [Box(60, 40, 740, 170), Box(80, 190, 720, 350)]
    assert plan_regions(800, 400, fragments) is None


def test_plan_regions_keeps_separate_page_equations() -> None:
    page_boxes = [Box(200, 300, 1400, 420), Box(200, 900, 1400, 1020)]
    regions = plan_regions(1700, 2300, page_boxes)
    assert regions == [Box(200, 300, 1400, 420), Box(200, 900, 1400, 1020)]


def test_plan_regions_small_image_without_detection_is_a_formula() -> None:
    assert plan_regions(600, 200, []) is None
    assert plan_regions(600, 200, [], assume_small_is_formula=False) == []


def test_plan_regions_large_empty_page_returns_no_regions() -> None:
    assert plan_regions(2500, 3500, []) == []


def test_padded_crop_box_stays_inside_the_image() -> None:
    padded = padded_crop_box(Box(0, 0, 100, 50), 120, 60)
    assert padded.left == 0 and padded.top == 0
    assert padded.right <= 120 and padded.bottom <= 60
    assert padded.right > 100 and padded.bottom > 50
