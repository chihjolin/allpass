import mlflow
from mlflow.pyfunc import PythonModel

mlflow.set_tracking_uri("http://localhost:5001")
mlflow.set_experiment("test_upgrade")

with mlflow.start_run():
    mlflow.log_param("param1", 123)
    mlflow.log_metric("metric1", 0.99)

class DummyModel(PythonModel):
    def predict(self, context, model_input):
        return model_input

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=DummyModel(),
    registered_model_name="upgrade_test_model"
)
