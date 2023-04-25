def test_generate_batches():
    route = [1, 2, 3, 4, 5]
    coordinate_count = 2
    batches = tracker.generate_batches(route, coordinate_count)
    assert (batches == [[1, 2], [3, 4], [5]])
