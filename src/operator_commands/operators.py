from src.omc_client import OMCClient


class OperatorCommands:

    def __init__(self, client: OMCClient):
        self.client = client

    # ============================================================
    # OLM OPERATORS
    # ============================================================

    def get_operators(self) -> str:
        """
        Get all installed OLM operators.

        Equivalent to:

            omc get operators
        """

        return self.client.run(
            [
                "get",
                "operators",
            ]
        )

    # ============================================================
    # CLUSTER OPERATORS
    # ============================================================

    def get_cluster_operators(self) -> str:
        """
        Get OpenShift ClusterOperators.

        Equivalent to:

            omc get clusteroperators
        """

        return self.client.run(
            [
                "get",
                "clusteroperators",
            ]
        )

    # ============================================================
    # OPERATOR NAMESPACE RESOURCES
    # ============================================================

    def get_operator_pods(
        self,
        namespace: str,
    ) -> str:
        """
        Get pods running in the operator namespace.

        Equivalent to:

            omc get pods -n <namespace>
        """

        return self.client.run(
            [
                "get",
                "pods",
                "-n",
                namespace,
            ]
        )

    def get_operator_events(
        self,
        namespace: str,
    ) -> str:
        """
        Get events from the operator namespace.

        Equivalent to:

            omc get events -n <namespace>
        """

        return self.client.run(
            [
                "get",
                "events",
                "-n",
                namespace,
            ]
        )

    def get_operator_deployments(
        self,
        namespace: str,
    ) -> str:
        """
        Get deployments from the operator namespace.

        Equivalent to:

            omc get deployments -n <namespace>
        """

        return self.client.run(
            [
                "get",
                "deployments",
                "-n",
                namespace,
            ]
        )

    def get_operator_replicasets(
        self,
        namespace: str,
    ) -> str:
        """
        Get ReplicaSets from the operator namespace.

        Equivalent to:

            omc get replicasets -n <namespace>
        """

        return self.client.run(
            [
                "get",
                "replicasets",
                "-n",
                namespace,
            ]
        )