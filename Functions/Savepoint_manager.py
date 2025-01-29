from PyQt6 import QtSql as QtS

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
        self.savepoint_list.append(savepoint_name)
        # print(self.savepoint_list)

    def remove_savepoint(self, savepoint_name: str):
        self.savepoint_list.remove(savepoint_name)
        # print(self.savepoint_list)

    def rollback_savepoint(self, savepoint_name: str):
        self.savepoint_list.remove(savepoint_name)
        # print(self.savepoint_list)

    def active_savepoints(self):
        return self.savepoint_list

def create_savepoint(savepoint_name: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'SAVEPOINT {savepoint_name}'):
        print(f'Failed to create savepoint {savepoint_name}: {query.lastError().text()}')
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.add_savepoint(savepoint_name)

def release_savepoint(savepoint_name: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'RELEASE SAVEPOINT {savepoint_name}'):
        print(f'Failed to release savepoint {savepoint_name}: {query.lastError().text()}')
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.remove_savepoint(savepoint_name)

def rollback_savepoint(savepoint_name: str):
    query = QtS.QSqlQuery()
    if not query.exec(f'ROLLBACK TO SAVEPOINT {savepoint_name}'):
        print(f'Failed to rollback to savepoint {savepoint_name}: {query.lastError().text()}')
    savepoint_manager = SavepointManager.get_instance()
    savepoint_manager.rollback_savepoint(savepoint_name)
