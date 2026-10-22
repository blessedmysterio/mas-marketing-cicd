#!/usr/bin/env sh
# Builds jenkins/kubeconfig so the Jenkins container can reach Minikube.
# Run on the host after `minikube start --driver=docker`.
set -e
cd "$(dirname "$0")"
MINIKUBE_IP=$(minikube ip)
kubectl config view --context=minikube --minify --flatten \
  | sed "s|server: https://.*|server: https://${MINIKUBE_IP}:8443|" > kubeconfig
chmod 600 kubeconfig
echo "kubeconfig written for https://${MINIKUBE_IP}:8443"
echo "Now: docker compose -f docker-compose.yml -f docker-compose.cd.yml up -d"
