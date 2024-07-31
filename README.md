# 🚀 ArgoCD Demo

## 🌟 Overview

This project sets up a Minikube environment with Gitea and ArgoCD, and deploys a sample application. The setup includes:

- 🏠 A Minikube cluster.
- 🐙 Gitea for hosting Git repositories.
- 🚀 ArgoCD for continuous delivery.

## 🔧 Prerequisites

- 🚀 Minikube
- 🪄 Helm
- 🛠️ kubectl
- 🌐 curl
- 🧰 git

## 📜 Setup Instructions

1. **Clone the repository:**
    ```sh
    git clone https://github.com/wozniakpl/argo-demo.git
    cd argo-demo
    ```

2. **Run the main script:**
    ```sh
    python3 main.py
    ```

    This script will:
    - 🚀 Start Minikube if it is not already running.
    - ➕ Add the necessary Helm repositories.
    - ⚙️ Install Gitea and ArgoCD using Helm charts.
    - 🏗️ Create and configure a repository in Gitea.
    - 📦 Deploy ArgoCD and configure it to manage the sample application.
    - 🌐 Start a Minikube tunnel which will keep running until the user presses `ENTER`.

    **Context Note:** This script is designed to be idempotent. After making any changes, you can simply press `ENTER`, use the up arrow to recall the previous command, and start the `main.py` script from scratch. The script detects changes in the repositories within the `src/` directory. If you change anything in `src/argo`, it will reapply those changes to the cluster. Similarly, any changes in the `infra` repository will be committed and reflected in Gitea. Helm deployments are upgraded, so changing `*.values.yml` files will also be reflected in the cluster.

3. **To clean up and start from scratch:**
    ```sh
    python3 main.py --clean
    ```

    This will:
    - 🗑️ Delete the Minikube cluster.
    - 🧹 Remove Gitea tokens and application data.
    - 🚮 Remove local repositories.

4. **To clean up everything after you're done:**
    ```sh
    minikube delete
    ```

    **⚠️ Note:** It is important to use the `--clean` option next time if you have cleaned up. If the `gitea.token` is present, the script will try to use it, which may cause issues if the token is no longer valid or the environment has changed.

## 🛠️ Configuration Details

### 🐙 Gitea

- **Chart Name:** gitea-charts/gitea
- **Values File:** `gitea.values.yml`

### 🚀 ArgoCD

- **Chart Name:** argo/argo-cd
- **Values File:** `argo.values.yml`

## 🔑 Credentials

- **Gitea:**
    - 🌐 URL: [http://localhost:3000](http://localhost:3000)
    - 👤 Username: `gitea`
    - 🔑 Password: `gitea`

- **ArgoCD:**
    - 🌐 URL: [https://localhost:8443](https://localhost:8443)
    - 👤 Username: `admin`
    - 🔑 Password: Fetched from `argocd-initial-admin-secret` (visible in terminal)

## 🌐 Minikube Tunnel

- A Minikube tunnel is started during the setup process to expose the services.
- The tunnel will keep running until the user presses `ENTER` at the end of the script.
- This is necessary to keep the LoadBalancer services accessible.

## 📝 Notes

- The script creates a repository named `infra` in Gitea and populates it with the contents from `src/infra`.
- ArgoCD is configured to automatically sync and manage the application specified in `src/argo/application.yaml`.

## 🛠️ Troubleshooting

- Ensure that Minikube is installed and configured correctly.
- Verify that Helm and kubectl are installed and accessible from the command line.
- Check the status of Minikube using `minikube status`.

For more information, refer to the documentation of the individual tools and services used in this setup. 🚀
