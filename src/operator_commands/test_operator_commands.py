from src.omc_client import OMCClient
from src.operator_commands import OperatorCommands


def parse_operators(operator_output: str) -> list[dict]:
    """
    Parse output of:

        omc get operators

    Expected format:

        NAME                                                    AGE
        loki-operator.openshift-operators-redhat                284d

    Returns:

        [
            {
                "name": "loki-operator",
                "namespace": "openshift-operators-redhat",
            }
        ]
    """

    operators = []

    for line in operator_output.splitlines():

        line = line.strip()

        # Ignore empty lines
        if not line:
            continue

        # Ignore header
        if line.startswith("NAME"):
            continue

        parts = line.split()

        if not parts:
            continue

        operator_namespace = parts[0]

        # Operator output uses:
        #
        # operator.namespace
        #
        # Split only on the first "."
        if "." not in operator_namespace:
            print(
                f"[WARNING] Unable to determine namespace: "
                f"{operator_namespace}"
            )
            continue

        operator_name, namespace = operator_namespace.split(
            ".",
            1,
        )

        operators.append(
            {
                "name": operator_name,
                "namespace": namespace,
            }
        )

    return operators


def main():

    # ---------------------------------------------------------
    # Initialize OMC
    # ---------------------------------------------------------

    omc_client = OMCClient()

    must_gather = input(
        "Enter must-gather path: "
    ).strip()

    print("\nLoading must-gather...\n")

    print(
        omc_client.use(must_gather)
    )

    operator_commands = OperatorCommands(
        omc_client
    )

    # ---------------------------------------------------------
    # Get ClusterOperators
    # ---------------------------------------------------------

    print(
        "\n========== CLUSTER OPERATORS ==========\n"
    )

    cluster_operator_output = (
        operator_commands.get_cluster_operators()
    )

    print(
        cluster_operator_output
    )

    # ---------------------------------------------------------
    # Get OLM Operators
    # ---------------------------------------------------------

    print(
        "\n========== OLM OPERATORS ==========\n"
    )

    operator_output = (
        operator_commands.get_operators()
    )

    print(
        operator_output
    )

    # ---------------------------------------------------------
    # Parse operator names + namespaces
    # ---------------------------------------------------------

    operators = parse_operators(
        operator_output
    )

    print(
        "\n========== PARSED OPERATORS ==========\n"
    )

    for operator in operators:

        print(
            f"Operator  : {operator['name']}"
        )

        print(
            f"Namespace  : {operator['namespace']}"
        )

        print()

    print(
        f"Total operators found: {len(operators)}"
    )

    # ---------------------------------------------------------
    # Collect details for every operator
    # ---------------------------------------------------------

    for operator in operators:

        operator_name = operator["name"]
        namespace = operator["namespace"]

        print(
            "\n"
            + "=" * 80
        )

        print(
            f"OPERATOR: {operator_name}"
        )

        print(
            f"NAMESPACE: {namespace}"
        )

        print(
            "=" * 80
        )

        # -----------------------------------------------------
        # Pods
        # -----------------------------------------------------

        # # print(
        # #     f"\n----- PODS: {namespace} -----\n"
        # # )

        # # try:

        # #     pods = (
        # #         operator_commands
        # #         .get_operator_pods(namespace)
        # #     )

        # #     print(pods)

        # # except Exception as exc:

        # #     print(
        # #         f"[ERROR] Failed to get pods: {exc}"
        # #     )

        # # # -----------------------------------------------------
        # # # Events
        # # # -----------------------------------------------------

        # # print(
        # #     f"\n----- EVENTS: {namespace} -----\n"
        # # )

        # # try:

        # #     events = (
        # #         operator_commands
        # #         .get_operator_events(namespace)
        # #     )

        # #     print(events)

        # # except Exception as exc:

        # #     print(
        # #         f"[ERROR] Failed to get events: {exc}"
        # #     )

        # # # -----------------------------------------------------
        # # # Deployments
        # # # -----------------------------------------------------

        # # print(
        # #     f"\n----- DEPLOYMENTS: {namespace} -----\n"
        # # )

        # # try:

        # #     deployments = (
        # #         operator_commands
        # #         .get_operator_deployments(namespace)
        # #     )

        # #     print(deployments)

        # # except Exception as exc:

        # #     print(
        # #         f"[ERROR] Failed to get deployments: {exc}"
        # #     )

        # # # -----------------------------------------------------
        # # # ReplicaSets
        # # # -----------------------------------------------------

        # # print(
        # #     f"\n----- REPLICASETS: {namespace} -----\n"
        # # )

        # # try:

        # #     replicasets = (
        # #         operator_commands
        # #         .get_operator_replicasets(namespace)
        # #     )

        # #     print(replicasets)

        # except Exception as exc:

        #     print(
        #         f"[ERROR] Failed to get ReplicaSets: {exc}"
        #     )


if __name__ == "__main__":
    main()