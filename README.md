# Month 5: Enterprise DevOps Practices — simplest KIND lab

One tiny Python app. No database, frameworks, passwords, or cloud bill.


1. **Kubernetes**: build and deploy a container on KIND.
2. **GitOps**: Argo CD watches GitHub and applies changes to Kubernetes.
3. **Monitoring**: Prometheus scrapes `/metrics` every 10 seconds.
4. **Alerting**: Prometheus raises an alert when the app is down.
5. **Cost optimization**: reduce replicas and CPU/memory requests (resource *planning*, not actual cloud billing).

## Files

- `app/server.py`: small website at `/`, readiness endpoint at `/health`, metrics endpoint at `/metrics`.
- `Dockerfile`: turns the app into an image.
- `kind/cluster.yaml`: one control-plane node and one worker.
- `k8s/`: app Namespace, Deployment, Service (also the Argo CD watched directory).
- `monitoring/all.yaml`: a simple Prometheus server and one alert rule.
- `argocd/application.yaml`: Argo CD Application (update GitHub URL first).

## Before class

Install Docker, KIND and kubectl. Check:

```bash
docker --version
kind version
kubectl version --client
```

## Lab 1: build and run locally on KIND

From this project's root directory:

```bash
kind create cluster --name devops-class --config kind/cluster.yaml
docker build -t devops-demo:v1 .
kind load docker-image devops-demo:v1 --name devops-class
kubectl apply -f k8s/
kubectl get pods -n demo
kubectl rollout status deployment/demo-app -n demo
```

Visit http://localhost:8080 in your browser. Visit http://localhost:8080/health and http://localhost:8080/metrics too. The NodePort Service uses port `30080`, and `kind/cluster.yaml` maps it to port `8080` on your computer.

For an existing KIND cluster created without that port mapping, use `http://<reachable-node-ip>:30080`, or temporarily run `kubectl port-forward -n demo service/demo-app 8080:80` and visit http://localhost:8080. The localhost NodePort mapping requires creating the cluster with the provided configuration; editing the configuration does not update an existing cluster.

Useful commands:

```bash
kubectl get all -n demo
kubectl logs -n demo deployment/demo-app
kubectl describe deployment demo-app -n demo
```

## Lab 2: monitoring and alerting

```bash
kubectl apply -f monitoring/all.yaml
kubectl rollout status deployment/prometheus -n monitoring
kubectl port-forward -n monitoring service/prometheus 9090:9090
```

Open http://localhost:9090. In the Prometheus query box, enter `up{job="demo-app"}` (expect `1` when healthy) or `demo_requests_total`. Refresh your app home page several times to increase the metric. Go to **Alerts** to see `DemoAppDown`.

**Trigger an alert** (from another terminal):

```bash
kubectl scale deployment/demo-app -n demo --replicas=0
```

Wait a bit over 30 seconds plus scrape/evaluation delay, then refresh Prometheus **Alerts**; `DemoAppDown` should become firing. Restore the app:

```bash
kubectl scale deployment/demo-app -n demo --replicas=1
```

This lab shows alerts in the Prometheus UI; it does **not** send email or Slack notifications. For production you would configure Alertmanager and notification receivers. Prometheus uses temporary storage here: its history is lost if the Prometheus pod is replaced.

## Lab 3: Argo CD GitOps

**Important:** The `devops-demo:v1` image in Lab 1 exists only inside KIND. For real GitOps, push your image to a *public container registry* (Docker Hub is an option), then change `image:` in `k8s/deployment.yaml` to `YOUR-DOCKERHUB-USERNAME/devops-demo:v1`. Make a public GitHub repository containing this project, and push the project there. Future source-code changes require rebuilding and pushing a **new image tag**, then updating `k8s/deployment.yaml` in Git. Editing `replicas` or resource requests in Git needs no image rebuild.

Install Argo CD:

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl rollout status deployment/argocd-server -n argocd --timeout=300s
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

Open https://localhost:8081 (accept the local self-signed certificate warning). Username is `admin`. Read the generated initial password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
```

Edit `argocd/application.yaml`: replace `YOUR-USERNAME` with your actual GitHub username; ensure the repository URL is correct. Then:

```bash
kubectl apply -f argocd/application.yaml
kubectl get applications -n argocd
```

In the Argo CD UI, inspect your `demo-app` Application. **Demo:** edit `replicas: 1` to `replicas: 2` in GitHub, commit, and let Argo CD sync. Compare `kubectl get pods -n demo` before and after. It may take a few minutes for automatic Git polling. You can also click **Refresh** and **Sync** in the Argo CD UI.

**GitOps warning:** once Argo CD manages `k8s/`, do not use `kubectl scale` as your normal method of changing replicas: self-heal can revert the manual change. Do the alert test in Lab 2 *before* enabling Argo CD, or trigger downtime by committing `replicas: 0` to Git and then restoring `replicas: 1`.

**If your computer is low on memory:** complete Lab 1 first, then Lab 2; remove monitoring before adding Argo CD using `kubectl delete -f monitoring/all.yaml`.

## Lab 4: resource and cost optimization

Read the resource block in `k8s/deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 25m
    memory: 32Mi
  limits:
    cpu: 200m
    memory: 128Mi
```

- `requests`: resources Kubernetes reserves for **scheduling** a pod.
- `limits`: maximum allowed (CPU can throttle; memory overuse can cause OOMKills).
- `replicas`: how many copies of your app run.

Experiment in Git: change replicas from `2` to `1` and observe the number of pods. Compare total requested CPU and RAM: for example, 2 pods x 25m CPU = 50m requested CPU, whereas 1 pod x 25m = 25m. This is **not a currency saving inside KIND**: KIND is local and you don't pay cloud instance rates. On AWS/EKS, reducing requests can help use nodes more efficiently, *and may* reduce spend if node capacity can actually be reduced.

See resource requests:

```bash
kubectl describe deployment demo-app -n demo
kubectl get pods -n demo
```

`kubectl top pods -n demo` works **only if metrics-server is installed** (it is not included in this lab). Prometheus `/metrics` currently tracks app requests, **not pod CPU/RAM**. For a later advanced lesson add metrics-server, kube-state-metrics and node-exporter, then Grafana and Alertmanager.

## Teaching order

- Session 1: KIND, Docker image, app deployment and Service.
- Session 2: Prometheus metrics and trigger/resolution of an alert.
- Session 3: Git repository, Argo CD automatic sync, and Git-based changes.
- Session 4: CPU/memory requests, replica sizing, and cloud cost discussion.

## Clean up

```bash
kind delete cluster --name devops-class
```

## Important

This is a **learning lab**, not a production-ready deployment: no TLS for the demo app, no persistent monitoring data, no Alertmanager notifications, and no production high availability. Public registry/repo instructions are for simplicity; a private setup is also possible with credentials.
# devops-month5
