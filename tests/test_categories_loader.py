from budget.infrastructure.config_loader.categories_loader import CategoryRepository


def test_category_repository_load_basic(tmp_path, monkeypatch):
    # create a temporary categories.csv
    csv_path = tmp_path / "categories.csv"
    csv_path.write_text("Category,Planned\nFood,100\nTransport,50\n")

    # Monkeypatch working directory so resolution finds this file first
    monkeypatch.chdir(tmp_path)

    repo = CategoryRepository()
    expense_cats, income_cats, planned_expenses, planned_income = repo.load()
    # Since our csv only had expense categories they should appear in expense list
    assert "Food" in expense_cats
    assert "Transport" in expense_cats
    assert planned_expenses.get("Food") == 100
    assert planned_expenses.get("Transport") == 50
