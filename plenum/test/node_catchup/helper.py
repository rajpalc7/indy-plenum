from typing import Iterable

from plenum.common.constants import POOL_LEDGER_ID, DOMAIN_LEDGER_ID
from stp_core.loop.eventually import eventually
from stp_core.types import HA
from plenum.test.helper import checkLedgerEquality, checkStateEquality
from plenum.test.test_client import TestClient
from plenum.test.test_node import TestNode
from plenum.test import waits
from plenum.common import util

# TODO: This should just take an arbitrary number of nodes and check for their
#  ledgers to be equal


def checkNodeDataForEquality(node: TestNode,
                             *otherNodes: Iterable[TestNode]):
    # Checks for node's ledgers and state's to be equal
    for n in otherNodes:
        checkLedgerEquality(node.domainLedger, n.domainLedger)
        checkLedgerEquality(node.poolLedger, n.poolLedger)
        for lid in (POOL_LEDGER_ID, DOMAIN_LEDGER_ID):
            checkStateEquality(node.getState(lid), n.getState(lid))


def waitNodeDataEquality(looper,
                         referenceNode: TestNode,
                         *otherNodes: Iterable[TestNode],
                         customTimeout=None):
    """
    Wait for node ledger to become equal

    :param referenceNode: node whose ledger used as a reference
    """

    numOfNodes = len(otherNodes) + 1
    timeout = customTimeout or waits.expectedPoolLedgerCheck(numOfNodes)
    looper.run(eventually(checkNodeDataForEquality,
                          referenceNode,
                          *otherNodes,
                          retryWait=1, timeout=timeout))


def ensureNewNodeConnectedClient(looper, client: TestClient, node: TestNode):
    stackParams = node.clientStackParams
    client.nodeReg[stackParams['name']] = HA('127.0.0.1', stackParams['ha'][1])
    looper.run(client.ensureConnectedToNodes())


def checkClientPoolLedgerSameAsNodes(client: TestClient,
                                     *nodes: Iterable[TestNode]):
    for n in nodes:
        checkLedgerEquality(client.ledger, n.poolLedger)


def ensureClientConnectedToNodesAndPoolLedgerSame(looper,
                                                  client: TestClient,
                                                  *nodes:Iterable[TestNode]):
    fVal = util.getMaxFailures(len(nodes))
    poolCheckTimeout = waits.expectedPoolLedgerCheck(fVal)
    looper.run(eventually(checkClientPoolLedgerSameAsNodes,
                          client,
                          *nodes,
                          timeout=poolCheckTimeout))
    looper.run(client.ensureConnectedToNodes())
