from export_unresolved_series_review import ADMIN_EDIT_COLUMNS, build_group_pivot


def test_build_group_pivot_sums_and_sorts():
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
        {"canonical_brand": "A", "raw_series": "X2", "canonical_series": "X", "total_units": 5, "status": "unreviewed"},
        {"canonical_brand": "B", "raw_series": "Y1", "canonical_series": "Y", "total_units": 3, "status": "conflicting"},
    ]
    grouped, grand_total = build_group_pivot(queue)

    assert grand_total == 18
    assert list(grouped["total_units"]) == [15, 3]
    assert grouped.iloc[0]["raw_variant_count"] == 2
    assert abs(grouped["cumulative_share"].iloc[-1] - 1.0) < 1e-9


def test_admin_edit_columns_appended_blank():
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
    ]
    grouped, _ = build_group_pivot(queue)

    expected_tail = ["canonical_brand", "canonical_series", "raw_variant_count", "raw_series_examples",
                      "total_units", "share_of_unresolved_na", "cumulative_share"] + ADMIN_EDIT_COLUMNS
    assert list(grouped.columns) == expected_tail
    for col in ADMIN_EDIT_COLUMNS:
        assert (grouped[col] == "").all()
