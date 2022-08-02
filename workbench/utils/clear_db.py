
''' This connects to the workbench server and tells it to clear the database..whee...'''
import zerorpc

if __name__ == "__main__":

    # Connect to workbench and tell it to clear itself
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")
    workbench.clear_db()
    print('Database completely wiped... Whee!')
