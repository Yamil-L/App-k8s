#!/bin/bash

# Script de verificación completa del clúster de Kubernetes
# Para el proyecto de Procesador de Texto

echo "=================================================="
echo "  VERIFICACIÓN DEL CLÚSTER DE KUBERNETES"
echo "=================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar comando
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ ERROR${NC}"
    fi
}

echo "1. ESTADO DE LOS NODOS"
echo "----------------------------------------"
kubectl get nodes -o wide
check_status
echo ""

echo "2. COMPONENTES DEL SISTEMA (kube-system)"
echo "----------------------------------------"
kubectl get pods -n kube-system
check_status
echo ""

echo "3. ESTADO DE COREDNS"
echo "----------------------------------------"
kubectl get pods -n kube-system -l k8s-app=kube-dns
check_status
echo ""

echo "4. ESTADO DE CONTAINERD"
echo "----------------------------------------"
echo "Verificando containerd en los nodos..."
for node in $(kubectl get nodes -o jsonpath='{.items[*].metadata.name}'); do
    echo "  Nodo: $node"
    kubectl get node $node -o jsonpath='{.status.nodeInfo.containerRuntimeVersion}'
    echo ""
done
check_status
echo ""

echo "5. VERIFICACIÓN DE PROMETHEUS"
echo "----------------------------------------"
kubectl get pods -A | grep prometheus
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Prometheus encontrado${NC}"
    kubectl get svc -A | grep prometheus
else
    echo -e "${YELLOW}⚠ Prometheus no encontrado${NC}"
fi
echo ""

echo "6. VERIFICACIÓN DE FLUENTD"
echo "----------------------------------------"
kubectl get pods -A | grep fluentd
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Fluentd encontrado${NC}"
    kubectl get daemonset -A | grep fluentd
else
    echo -e "${YELLOW}⚠ Fluentd no encontrado${NC}"
fi
echo ""

echo "7. VERIFICACIÓN DE FLUX"
echo "----------------------------------------"
kubectl get pods -A | grep flux
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Flux encontrado${NC}"
    flux check
else
    echo -e "${YELLOW}⚠ Flux no encontrado${NC}"
fi
echo ""

echo "8. NAMESPACES EXISTENTES"
echo "----------------------------------------"
kubectl get namespaces
check_status
echo ""

echo "9. TODOS LOS PODS EN EL CLÚSTER"
echo "----------------------------------------"
kubectl get pods --all-namespaces
check_status
echo ""

echo "10. SERVICIOS EXPUESTOS"
echo "----------------------------------------"
kubectl get svc --all-namespaces
check_status
echo ""

echo "11. RECURSOS DEL CLÚSTER"
echo "----------------------------------------"
kubectl top nodes 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Metrics server no disponible (necesario para 'kubectl top')${NC}"
fi
echo ""

echo "12. EVENTOS RECIENTES (últimos 10)"
echo "----------------------------------------"
kubectl get events --all-namespaces --sort-by='.lastTimestamp' | tail -20
echo ""

echo "13. PERSISTENT VOLUMES"
echo "----------------------------------------"
kubectl get pv
kubectl get pvc --all-namespaces
echo ""

echo "14. INGRESS CONTROLLERS"
echo "----------------------------------------"
kubectl get ingress --all-namespaces
echo ""

echo "=================================================="
echo "  RESUMEN DE VERIFICACIÓN"
echo "=================================================="
echo ""

# Contador de componentes críticos
CRITICAL_COMPONENTS=0
TOTAL_CHECKS=0

# Verificar nodos
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
READY_NODES=$(kubectl get nodes --no-headers | grep -c " Ready ")
TOTAL_NODES=$(kubectl get nodes --no-headers | wc -l)
echo "Nodos: $READY_NODES/$TOTAL_NODES Ready"
if [ "$READY_NODES" -eq "$TOTAL_NODES" ]; then
    CRITICAL_COMPONENTS=$((CRITICAL_COMPONENTS + 1))
    echo -e "${GREEN}✓ Todos los nodos están Ready${NC}"
else
    echo -e "${RED}✗ Algunos nodos no están Ready${NC}"
fi

# Verificar CoreDNS
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
COREDNS_RUNNING=$(kubectl get pods -n kube-system -l k8s-app=kube-dns --no-headers 2>/dev/null | grep -c "Running")
if [ "$COREDNS_RUNNING" -gt 0 ]; then
    CRITICAL_COMPONENTS=$((CRITICAL_COMPONENTS + 1))
    echo -e "${GREEN}✓ CoreDNS está funcionando ($COREDNS_RUNNING pods)${NC}"
else
    echo -e "${RED}✗ CoreDNS no está funcionando${NC}"
fi

# Verificar componentes del control plane
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
CONTROL_PLANE_PODS=$(kubectl get pods -n kube-system --no-headers | grep -E "kube-apiserver|kube-controller|kube-scheduler|etcd" | grep -c "Running")
if [ "$CONTROL_PLANE_PODS" -ge 4 ]; then
    CRITICAL_COMPONENTS=$((CRITICAL_COMPONENTS + 1))
    echo -e "${GREEN}✓ Componentes del control plane funcionando${NC}"
else
    echo -e "${YELLOW}⚠ Verificar componentes del control plane${NC}"
fi

echo ""
echo "Componentes críticos funcionando: $CRITICAL_COMPONENTS/$TOTAL_CHECKS"
echo ""

if [ "$CRITICAL_COMPONENTS" -eq "$TOTAL_CHECKS" ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}  ✓ CLÚSTER LISTO PARA DESPLIEGUES${NC}"
    echo -e "${GREEN}=========================================${NC}"
else
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}  ⚠ REVISAR COMPONENTES ANTES DE CONTINUAR${NC}"
    echo -e "${YELLOW}=========================================${NC}"
fi

echo ""
echo "Siguiente paso: Desplegar Frontend, Backend y Base de Datos"
echo "Crea un namespace para tu aplicación:"
echo "  kubectl create namespace text-processor"
echo ""