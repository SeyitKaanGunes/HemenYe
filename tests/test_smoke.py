def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_customer_login_page(client):
    response = client.get("/customer/login")
    assert response.status_code == 200


def test_restaurant_login_page(client):
    response = client.get("/restaurant/login")
    assert response.status_code == 200


def test_admin_login_page(client):
    response = client.get("/admin/login")
    assert response.status_code == 200


def test_customer_restaurants_page(client):
    response = client.get("/customer/restaurants")
    assert response.status_code == 200
