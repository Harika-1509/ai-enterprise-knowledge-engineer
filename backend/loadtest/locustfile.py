from locust import HttpUser, task, between


class AKEUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "YourPassword123"},
        )
        self.token = response.json().get("access_token")

    @task(3)
    def ask_simple_question(self):
        self.client.post(
            "/api/v1/agent/",
            json={"query": "What is the stipend?", "limit": 5},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(1)
    def search_documents(self):
        self.client.post(
            "/api/v1/search/",
            json={"query": "stipend", "limit": 5},
            headers={"Authorization": f"Bearer {self.token}"},
        )