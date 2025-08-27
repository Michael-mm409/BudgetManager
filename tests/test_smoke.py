def test_main_callable():
    import main  # noqa: F401

    assert callable(main.main)
