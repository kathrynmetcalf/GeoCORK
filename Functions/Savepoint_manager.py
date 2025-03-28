from PyQt6 import QtSql as QtS
from PyQt6.QtSql import QSqlDatabase

import logger_setup


class SavepointManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SavepointManager, cls).__new__(cls)
            cls._instance.savepoint_list = []
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    def add_savepoint(self, savepoint_name: str):
        if savepoint_name not in self.savepoint_list:
            self.savepoint_list.append(savepoint_name)
        # print(self.savepoint_list)

    def remove_savepoint(self, savepoint_name: str):
        if savepoint_name in self.savepoint_list:
            self.savepoint_list.remove(savepoint_name)
        # print(self.savepoint_list)

    def rollback_savepoint(self, savepoint_name: str):
        if savepoint_name in self.savepoint_list:
            self.savepoint_list.remove(savepoint_name)
        # print(self.savepoint_list)

    def active_savepoints(self):
        return self.savepoint_list

def create_savepoint(savepoint_name: str, database: QSqlDatabase=QSqlDatabase()):
    """
    Function to create a savepoint on the given database.
    :param str savepoint_name: string of the savepoint name to rollback
    :param QSqlDatabase database: database to create on, if not provided to default connection
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery()
    logger_setup.get_logger().info(f'Creating savepoint {savepoint_name} on {database.connectionName()}')
    if not query.exec(f'SAVEPOINT {savepoint_name}'):
        logger_setup.get_logger().critical(f'Failed to create savepoint {savepoint_name}')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        return False
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.add_savepoint(savepoint_name)
    return True

def release_savepoint(savepoint_name: str, database : QSqlDatabase=QSqlDatabase()) -> bool:
    """
    Function to release the savepoint on the given database.
    :param str savepoint_name: string of the savepoint name to rollback
    :param QSqlDatabase database: database to release on, if not provided to default connection
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery(database)
    logger_setup.get_logger().info(f'Releasing savepoint {savepoint_name} on {database.connectionName()}')
    if not query.exec(f'RELEASE SAVEPOINT {savepoint_name}'):
        logger_setup.get_logger().info(f'Savepoint {savepoint_name} already released')
        logger_setup.get_logger().debug(f'Error: {query.lastError().text()}')
        return False
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.remove_savepoint(savepoint_name)
    return True

def rollback_savepoint(savepoint_name: str, database : QSqlDatabase=QSqlDatabase()) -> bool:
    """
    Function to roll back the given database to the provided savepoint name.
    :param str savepoint_name: string of the savepoint name to rollback
    :param QSqlDatabase database: database to rollback on, if not provided to default connection
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery(database)
    logger_setup.get_logger().info(f'Rolling back to savepoint {savepoint_name} on {database.connectionName()}')
    if not query.exec(f'ROLLBACK TO SAVEPOINT {savepoint_name}'):
        logger_setup.get_logger().critical(f'Failed to undo changes')
        logger_setup.get_logger().debug(f'Failed to rollback to savepoint {savepoint_name}: {query.lastError().text()}')
        return False
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.rollback_savepoint(savepoint_name)
    return True
