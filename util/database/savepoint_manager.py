from PyQt6 import QtSql as QtS
from PyQt6.QtSql import QSqlDatabase

from util import geocork_logger


class SavepointManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.savepoint_list = []
            cls._instance = instance
        return cls._instance

    @classmethod
    def reset(cls):
        """
        Clear all savepoints and drop the singleton
        :return:
        """
        if cls._instance is not None:
            cls._instance.savepoint_list.clear()
        cls._instance = None

    @classmethod
    def get_instance(cls) -> "SavepointManager":
        """
        Return the singleton, creating it on first use.
        :return:
        """
        return cls()

    def add_savepoint(self, savepoint_name: str):
        if savepoint_name not in self.savepoint_list:
            self.savepoint_list.append(savepoint_name)

    def remove_savepoint(self, savepoint_name: str):
        if savepoint_name in self.savepoint_list:
            self.savepoint_list.remove(savepoint_name)

    def active_savepoints_names(self) -> list:
        """
        Returns a list of active savepoint names.
        :return: list of active savepoint names
        :rtype: list
        """
        return list(self.savepoint_list)

    def active_savepoints(self) -> bool:
        """
        Returns if active savepoints exist.
        :return: True if savepoints exist, False otherwise
        :rtype: bool
        """
        return bool(self.savepoint_list)

def create_savepoint(savepoint_name: str, database: QSqlDatabase=QSqlDatabase()):
    """
    Function to create a savepoint on the given database.
    :param str savepoint_name: string of the savepoint name to rollback
    :param QSqlDatabase database: database to create on, if not provided to default connection
    :return: True for success, False for failure
    :rtype: bool
    """
    query = QtS.QSqlQuery()
    geocork_logger.get_logger().info(f'Creating savepoint {savepoint_name} on {database.connectionName()}')
    if not query.exec(f'SAVEPOINT {savepoint_name}'):
        geocork_logger.get_logger().critical(f'Failed to create savepoint before making changes')
        geocork_logger.get_logger().debug(f'Error: {query.lastError().text()}')
        geocork_logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
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
    geocork_logger.get_logger().info(f'Releasing savepoint {savepoint_name} on connection {database.connectionName()}')
    if not query.exec(f'RELEASE SAVEPOINT {savepoint_name}'):
        if 'no such savepoint' in query.lastError().text():
            geocork_logger.get_logger().info(f'Savepoint {savepoint_name} already released')
            geocork_logger.get_logger().debug(f'Error: {query.lastError().text()}')
            geocork_logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
            savepoint_manager = SavepointManager.get_instance()
            savepoint_manager.remove_savepoint(savepoint_name)
            return False
        else:
            geocork_logger.get_logger().info(f'Error releasing {savepoint_name}')
            geocork_logger.get_logger().debug(f'Error: {query.lastError().text()}')
            geocork_logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
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
    geocork_logger.get_logger().info(f'Rolling back to savepoint {savepoint_name} on {database.connectionName()}')
    if not query.exec(f'ROLLBACK TO SAVEPOINT {savepoint_name}'):
        if 'no such savepoint' in query.lastError().text():
            geocork_logger.get_logger().info(f'Savepoint {savepoint_name} already rolled back')
            geocork_logger.get_logger().debug(f'Error: {query.lastError().text()}')
            geocork_logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
            savepoint_manager = SavepointManager.get_instance()
            savepoint_manager.remove_savepoint(savepoint_name)
        else:
            geocork_logger.get_logger().critical(f'Failed to undo changes')
            geocork_logger.get_logger().debug(f'Failed to rollback to savepoint {savepoint_name}: {query.lastError().text()}')
            geocork_logger.get_logger().debug(f'SQL query: {query.lastQuery()}')
            return False
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.remove_savepoint(savepoint_name)
    return True
