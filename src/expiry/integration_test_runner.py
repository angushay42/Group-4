from django.test.runner import DiscoverRunner

class IntegrationRunner(DiscoverRunner):
    def setup_databases(*args, **kwargs):
        pass

    def teardown_databases(*args, **kwargs):
        pass