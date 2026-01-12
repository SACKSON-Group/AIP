# @pytest.fixture(scope="function")
# def test_db():
#     Base.metadata.create_all(bind=test_engine)
#     yield
#     Base.metadata.drop_all(bind=test_engine)

# def test_create_project(test_db):
#     response = client.post(
#         "/projects/",
#         json={"name": "Test Project", "sector": "Energy", "country": "Nigeria"}
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert data["name"] == "Test Project"
#     assert data["verification_level"] == 0