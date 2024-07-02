import os
import subprocess
from contextlib import contextmanager
import json

token_file = "gitea.token"
application_data_file = "gitea.ci.app.json"


def get_api_token(svc_ip, svc_port):
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            return f.read()

    username = "gitea"
    password = "gitea"

    command = f"""\
curl -s -u {username}:{password} \
    -X POST "http://{svc_ip}:{svc_port}/api/v1/users/{username}/tokens" \
    -H "Content-Type: application/json" \
    -d '{{"name": "automation-token", "scopes": ["all"]}}' \
"""
    response = os.popen(command).read().strip()
    api_token = json.loads(response)["sha1"]

    with open(token_file, "w") as f:
        f.write(api_token)

    return api_token


def create_repo(app_name, svc_ip, port):
    api_token = get_api_token(svc_ip, port)
    check_if_repo_exists_command = f"""\
curl -s -o /dev/null -w "%{{http_code}}" \
    -X GET "http://{svc_ip}:{port}/api/v1/repos/gitea/{app_name}" \
    -H "Authorization: token {api_token}" \
"""
    print(f"Checking if repo '{app_name}' exists")
    response = os.popen(check_if_repo_exists_command).read().strip()
    if response != "200":
        create_repo_command = f"""\
curl -s \
    -X POST "http://{svc_ip}:{port}/api/v1/admin/users/gitea/repos" \
    -H "Authorization: token {api_token}" \
    -H "Content-Type: application/json" \
    -d '{{"name": "{app_name}", "description": "foobar", "private": false}}' \
"""
        os.system(create_repo_command)
    else:
        print("Repo already exists")


def get_svc_ip_and_port(namespace, svc_name):
    get_svc_ip_command = f"kubectl get svc --namespace {namespace} {svc_name} -o jsonpath='{{.status.loadBalancer.ingress[0].ip}}'"
    svc_ip = ""
    while svc_ip == "":
        svc_ip = os.popen(get_svc_ip_command).read().strip()

    get_svc_port_command = f"kubectl get svc --namespace {namespace} {svc_name} -o jsonpath='{{.spec.ports[0].port}}'"
    port = os.popen(get_svc_port_command).read().strip()

    return svc_ip, port


def configure_gitea():
    namespace = "gitea"
    chart_name = "gitea-charts/gitea"
    upgrade_command = f"helm upgrade --install gitea {chart_name} --namespace {namespace} --create-namespace -f gitea.values.yml"
    os.system(upgrade_command)

    wait_command = f"kubectl wait --namespace {namespace} --for=condition=available deployment/gitea --timeout=300s"
    os.system(wait_command)

    gitea_svc = "gitea-http"
    svc_ip, svc_port = get_svc_ip_and_port(namespace, gitea_svc)
    print(f"Gitea is running at http://{svc_ip}:{svc_port}")
    print("Credentials: gitea : gitea")

    create_repo("infra", svc_ip, svc_port)


def configure_argo():
    namespace = "argo"
    chart_name = "argo/argo-cd"
    upgrade_command = f"helm upgrade --install argo {chart_name} --namespace {namespace} --create-namespace -f argo.values.yml"
    os.system(upgrade_command)

    wait_command = f"kubectl wait --namespace {namespace} --for=condition=available deployment/argo-argocd-server --timeout=300s"
    os.system(wait_command)

    argo_svc = "argo-argocd-server"
    svc_ip, svc_port = get_svc_ip_and_port(namespace, argo_svc)
    print(f"Argo is running at http://{svc_ip}:{svc_port}")

    password = (
        os.popen(
            f"kubectl -n argo get secret argocd-initial-admin-secret -o jsonpath={{.data.password}} | base64 -d"
        )
        .read()
        .strip()
    )
    print(f"Credentials: admin : {password}")

    apply_self_manage_command = f"kubectl apply -f src/argo/"
    os.system(apply_self_manage_command)

    image_updater_command = f"kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"
    os.system(image_updater_command)


def clone_repo(username, repo_name, svc_ip, port):
    os.system(f"mkdir repos")
    os.system(
        f"git clone http://{svc_ip}:{port}/{username}/{repo_name}.git repos/{repo_name}"
    )


def configure_infra_repo():
    svc_ip, svc_port = get_svc_ip_and_port("gitea", "gitea-http")
    clone_repo("gitea", "infra", svc_ip, svc_port)
    os.system("cp -r src/infra/* repos/infra")
    os.system("cd repos/infra && git add . ; git commit -m 'foobar' ; git push")


@contextmanager
def minikube_tunnel():
    os.system("minikube tunnel &")
    try:
        yield
    finally:
        os.system("pkill -f 'minikube tunnel'")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Start from scratch")
    return parser.parse_args()


def main():
    args = parse_args()

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    if args.clean:
        os.system(f"rm {token_file}")
        os.system(f"rm {application_data_file}")
        os.system("rm -rf ./repos")
        os.system("minikube delete")

    status = os.system("minikube status")
    if status != 0:
        os.system("minikube start")
    else:
        print("Minikube is already running")

    result = subprocess.Popen(["helm", "repo", "list"], stdout=subprocess.PIPE)
    repos = result.stdout.read().decode("utf-8")

    def add_helm_repo(repo_name, repo_url):
        repo_lines = [line for line in repos.split("\n") if repo_name in line]
        if len(repo_lines) == 0:
            os.system(f"helm repo add {repo_name} {repo_url}")
        else:
            print(f"{repo_name} repo already added")

    add_helm_repo("gitea-charts", "https://dl.gitea.io/charts/")
    add_helm_repo("argo", "https://argoproj.github.io/argo-helm")
    add_helm_repo("vquie", "https://vquie.github.io/helm-charts")
    add_helm_repo("bitnami", "https://charts.bitnami.com/bitnami")

    with minikube_tunnel():
        configure_gitea()
        configure_infra_repo()
        configure_argo()

        input("Press ENTER to exit and stop minikube tunnel")


if __name__ == "__main__":
    main()
