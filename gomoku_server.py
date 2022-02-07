#!/bin/python3
from socket import *
import sys
import signal
from select import select
import time
import math


BUF_SIZE = 3
MAX_CLIENT_LENGTH = 2
CMD_CONNECT = 0
CMD_READY = 1
CMD_UPDATE = 2
CMD_PUT = 3
CMD_END = 4

WHITE = 1
BLACK = 0
BLANK = -1

gomoku_map = [[-1 for i in range(15)] for i in range(15)]


def column(matrix, i):
    ret = []
    for row in matrix:
        ret.append(row[i])
    return ret


def diagonal(matrix, x, y):
    diag1 = []
    diag2 = []

    x_iter, y_iter = x, y
    while (x_iter > 0 and y_iter > 0):
        x_iter -= 1
        y_iter -= 1
    while (x_iter < 15 and y_iter < 15):
        diag1.append(matrix[x_iter][y_iter])
        x_iter += 1
        y_iter += 1
    
    x_iter, y_iter = x, y
    while (x_iter > 0 and y_iter < 14):
        x_iter -= 1
        y_iter += 1
    while (x_iter < 15 and y_iter > -1):
        diag2.append(matrix[x_iter][y_iter])
        x_iter += 1
        y_iter -= 1
    
    return diag1, diag2


def find_cannot_place(x_idx, y_idx, color_id):
    return False


def someone_win(x_idx, y_idx, color_id):
    row = gomoku_map[x_idx]
    col = column(gomoku_map, y_idx)
    diag = diagonal(gomoku_map, x_idx, y_idx)

    for candidate in [row, col, *diag]:
        length = 0
        length_list = []
        for i in range(len(candidate)):
            if candidate[i] == color_id:
                length += 1
            else:
                length_list.append(length)
                length = 0
        
        if color_id == BLACK:
            try:
                id = length_list.index(5)
                return True
            except ValueError:
                continue
        else:
            if length_list and max(length_list) >= 5:
                return True

    return False


def put(color_id, x, y):

    x_idx = x-1
    y_idx = y-1

    if not(0 < x < 16 and 0 < y < 16) :
        return 1

    if gomoku_map[x_idx][y_idx] != -1:
        return 1

    if find_cannot_place(x_idx, y_idx, color_id):
        return 1
    
    gomoku_map[x_idx][y_idx] = color_id

    if someone_win(x_idx, y_idx, color_id):
        return 2
    
    return 0


def make_bytes(cmd: int, turn: int, data: int):
    return bytes([cmd, turn, data])


def handler(signal, frame):
    print("\nBye bye~")
    for ir in input_ready:
        ir.close()
    if serverSocket:
        serverSocket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

serverPort = 1234
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))
serverSocket.listen()
print("server is ready to receive on port", serverPort)

input_list = [serverSocket]
connectionSocket_list = []
is_start = False
ready_status = [0, 0]
turn_status = [0, 0]
color_status = (0, 1)

while True:
    input_ready, write_ready, except_ready = select(input_list, [], [])
    for ir in input_ready:
        
        if ir == sys.stdin:
            junk = sys.stdin.readline()
        
        if not is_start:                                                    # before start
            if ir == serverSocket:
                (connectionSocket, clientAddress) = serverSocket.accept()
                input_list.append(connectionSocket)
                print("connection: ", connectionSocket, clientAddress)
            
            else:
                msg = ir.recv(BUF_SIZE)

                if not msg:
                    try:
                        id = connectionSocket_list.index(ir)
                    except ValueError:
                        id = -1
                    if id != -1:
                        ready_status[id] = 0
                        connectionSocket_list.remove(ir)
                    ir.close()
                    input_list.remove(ir)
                    continue

                cmd, turn, data = int(msg[0]), int(msg[1]), int(msg[2])
                try:
                    id = connectionSocket_list.index(ir)
                except ValueError:
                    id = -1
                if id == -1:
                    if cmd == CMD_CONNECT:
                        print("connect")
                        if len(connectionSocket_list) >= MAX_CLIENT_LENGTH:
                            print("server is full")
                            ir.send(make_bytes(CMD_CONNECT, 2, 2))
                            ir.close()
                            input_list.remove(ir)
                        else:
                            ir.send(make_bytes(CMD_CONNECT, len(connectionSocket_list), 1))
                            connectionSocket_list.append(ir)
                    else:
                        ir.send(make_bytes(CMD_CONNECT, 2, 2))
                        ir.close()
                        input_list.remove(ir)
                
                elif cmd == CMD_READY:
                    ready_status[id] = data
                    if sum(ready_status) == 2:
                        is_start = True
                        turn_status[1] = 1
                        i = 0
                        for sock in connectionSocket_list:
                            sock.send(make_bytes(CMD_UPDATE, color_status[i], 0))
                            i += 1
                        start = time.time()
            continue
        
        if ir == sys.stdin:                                         # after start
            junk = sys.stdin.readline
        
        elif ir == serverSocket:
            (connectionSocket, clientAddress) = serverSocket.accept()
            connectionSocket.send(make_bytes(CMD_CONNECT, 2, 2))
            connectionSocket.close()
            
        else:
            msg = ir.recv(BUF_SIZE)
            
            if not msg:
                try:
                    id = connectionSocket_list.index(ir)
                except ValueError:
                    id = -1
                if id != -1:
                    ready_status = [0, 0]
                    connectionSocket_list.remove(ir)
                    ir.close()
                    input_list.remove(ir)
                    for sock in connectionSocket_list:
                        sock.send(make_bytes(CMD_END, 1, 0))
                        sock.close()
                        input_list.remove(sock)
                else:
                    ir.close()
                    input_list.remove(ir)
                continue

            cmd, turn, data = int(msg[0]), int(msg[1]), int(msg[2])

            if cmd == CMD_PUT:
                try:
                    id = connectionSocket_list.index(ir)
                except ValueError:
                    id = -1
                if turn_status[id] == 1:
                    ready_status = [0, 0]
                    connectionSocket_list.remove(ir)
                    ir.send(make_bytes(CMD_END, 0, 0))
                    ir.close()
                    input_list.remove(ir)
                    for sock in connectionSocket_list:
                        sock.send(make_bytes(CMD_END, 1, 0))
                        sock.close()
                        input_list.remove(sock)

                else:
                    end = time.time()    
                    x = data >> 4
                    y = data & 0b00001111
                    if math.floor(end - start) > 15:
                        ret = 3
                    else:
                        ret = put(color_status[id], x, y)
                    
                    if ret == 1:    # error
                        data_id = make_bytes(CMD_END, 0, 0)
                        data_not_id = make_bytes(CMD_END, 1, 0)
                        connectionSocket_list[id].send(data_id)
                        connectionSocket_list[int(not id)].send(data_not_id)
                        for sock in connectionSocket_list:
                            sock.close()
                            input_list.remove(sock)

                    elif ret == 2:  # win
                        data_not_id = make_bytes(CMD_END, 0, data)
                        data_id = make_bytes(CMD_END, 1, data)
                        connectionSocket_list[id].send(data_id)
                        connectionSocket_list[int(not id)].send(data_not_id)
                        for sock in connectionSocket_list:
                            sock.close()
                            input_list.remove(sock)

                    elif ret == 3:  # time out
                        data_id = make_bytes(CMD_END, 0, 1)
                        data_not_id = make_bytes(CMD_END, 1, 1)
                        connectionSocket_list[id].send(data_id)
                        connectionSocket_list[int(not id)].send(data_not_id)
                        for sock in connectionSocket_list:
                            sock.close()
                            input_list.remove(sock)

                    else:           # good
                        turn_status[0], turn_status[1] = turn_status[1], turn_status[0]
                        data0 = make_bytes(CMD_UPDATE, turn_status[0], data)
                        data1 = make_bytes(CMD_UPDATE, turn_status[1], data)
                        connectionSocket_list[0].send(data0)
                        connectionSocket_list[1].send(data1)

                start = time.time()

            else:
                ready_status = [0, 0]
                connectionSocket_list.remove(ir)
                ir.send(make_bytes(CMD_END, 0, 0))
                ir.close()
                input_list.remove(ir)
                for sock in connectionSocket_list:
                    sock.send(make_bytes(CMD_END, 1, 0))
                    sock.close()
                    input_list.remove(sock)
