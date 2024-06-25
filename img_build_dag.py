from datetime import datetime
from airflow.decorators import dag, task
from kubernetes.client import models as k8s
from airflow.models import Variable
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

@dag(
    description='esto es una demo',
    schedule_interval='0 12 * * *',
    start_date=datetime(2024, 4, 16),
    catchup=False,
    tags=['test', 'dag'],
)
def test_bash():

    env_vars={
        "POSTGRES_USERNAME": Variable.get("POSTGRES_USERNAME"),
        "POSTGRES_PASSWORD": Variable.get("POSTGRES_PASSWORD"),
        "POSTGRES_DATABASE": Variable.get("POSTGRES_DATABASE"),
        "POSTGRES_HOST": Variable.get("POSTGRES_HOST"),
        "POSTGRES_PORT": Variable.get("POSTGRES_PORT"),
        "TRUE_CONNECTOR_EDGE_IP": Variable.get("CONNECTOR_EDGE_IP"),
        "TRUE_CONNECTOR_EDGE_PORT": Variable.get("IDS_EXTERNAL_ECC_IDS_PORT"),
        "TRUE_CONNECTOR_CLOUD_IP": Variable.get("CONNECTOR_CLOUD_IP"),
        "TRUE_CONNECTOR_CLOUD_PORT": Variable.get("IDS_PROXY_PORT"),
        "MLFLOW_ENDPOINT": Variable.get("MLFLOW_ENDPOINT"),
        "MLFLOW_TRACKING_USERNAME": Variable.get("MLFLOW_TRACKING_USERNAME"),
        "MLFLOW_TRACKING_PASSWORD": Variable.get("MLFLOW_TRACKING_PASSWORD")
    }

    volume_mount = k8s.V1VolumeMount(
        name="dag-dependencies", mount_path="/git"
    )

    init_container_volume_mounts = [
        k8s.V1VolumeMount(mount_path="/git", name="dag-dependencies")
    ]

    volume = k8s.V1Volume(name="dag-dependencies", empty_dir=k8s.V1EmptyDirVolumeSource())

    init_container = k8s.V1Container(
        name="git-clone",
        image="alpine/git:latest",
        command=["sh", "-c", "mkdir -p /git && cd /git && git clone -b main --single-branch https://gitlab.com/mikel_fernandez/test-platform.git"],
        volume_mounts=init_container_volume_mounts
    )

    @task.kubernetes(
        task_id='build_push_image',
        name='build',
        namespace='airflow',
        image='mfernandezlabastida/kaniko:1.0',
        image_pull_policy='Always',
        init_containers=[init_container],
        volumes=[volume],
        volume_mounts=[volume_mount],
        env_vars=env_vars,
        do_xcom_push=True,
    )
    def img_build_task():
        # import subprocess
        import logging
        from kaniko import Kaniko, KanikoSnapshotMode

        path = '/git/DAG_image_build/docker/'

        logging.warning("Building and pushing image")
        kaniko = Kaniko()
        kaniko.build(
            dockerfile=f'{path}/Dockerfile',
            context=path,
            # docker_registry_uri='http://registry-docker-registry.registry.svc.cluster.local:5000/',
            destination='registry.registry.svc.cluster.local:5000/mfernandezlabastida/engine:1.0',
            snapshot_mode=KanikoSnapshotMode.full,
        )

    # build_push_image_result = build_push_image('docker')
    img_build_task_result = img_build_task()

    # Define the order of the pipeline
    img_build_task_result
# Call the DAG
test_bash()