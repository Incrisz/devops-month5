# Monitoring and Argo CD

Start with a working Kubernetes cluster, kubectl, and the demo app deployed. Run commands from this repository's root directory.

## Monitoring with Prometheus

Deploy Prometheus:

```bash
kubectl apply -f monitoring/all.yaml
kubectl rollout status deployment/prometheus -n monitoring
```

Open `http://<reachable-node-ip>:30500`. For KIND, configure the port mapping yourself.

Alternatively, run:

```bash
kubectl port-forward -n monitoring service/prometheus 9090:9090
```

Then open http://localhost:9090 and leave that terminal running.

In Prometheus, query `up{job="demo-app"}`. A value of `1` means the app is reachable; `0` means scraping failed. Open **Alerts** to see `DemoAppDown`.

### Test the alert before enabling Argo CD

Stop the app:

```bash
kubectl scale deployment/demo-app -n demo --replicas=0
```

After the next scrape and rule evaluation, the alert becomes pending. It fires after the failure persists for 30 seconds and the rule is evaluated again.

Restore the app:

```bash
kubectl scale deployment/demo-app -n demo --replicas=1
```

Alerts appear only in Prometheus; no email or Slack notifications are configured. Monitoring history is lost when the Prometheus pod is replaced.

## Argo CD

Argo CD watches the `k8s/` folder in GitHub and automatically applies its configuration to your cluster. The app image must already be available to the cluster; Argo CD does not build images.

### Install

Create the namespace if it does not already exist:

```bash
kubectl create namespace argocd
```

Install Argo CD before applying your Application:

```bash
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Established crd/applications.argoproj.io --timeout=120s
kubectl rollout status deployment/argocd-server -n argocd --timeout=300s
kubectl get pods -n argocd
```

### Connect your repository

Check that `repoURL` in `argocd/application.yaml` points to your public GitHub repository and that your Kubernetes files are committed in `k8s/`.

```bash
kubectl apply -f argocd/application.yaml
kubectl get applications -n argocd
```

### Open Argo CD

```bash
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

Leave this terminal running and open https://localhost:8081. Accept the local certificate warning.

Username: `admin`. In another terminal, get the initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

If port-forward runs on a remote server, `localhost` refers to that server. To open Argo CD from your computer, run this on your computer and keep it running:

```bash
ssh -L 8081:localhost:8081 ubuntu@<server-public-ip>
```

Then open https://localhost:8081 on your computer. Use your usual SSH key if required.

### Try GitOps

Change `replicas: 1` to `replicas: 2` in `k8s/deployment.yaml`, commit, and push. Argo CD detects the change and runs two copies of the app.

```bash
kubectl get pods -n demo
```

With `selfHeal: true`, Argo CD reverses manual changes that differ from Git. With `prune: true`, it deletes managed resources removed from Git. For an alert test after enabling Argo CD, commit and push `replicas: 0`, then restore it to `1` in Git.

Argo CD manages only `k8s/`; deploy monitoring separately using the commands above.
