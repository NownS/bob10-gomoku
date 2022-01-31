from gomoku_lib import Gomoku

my_gomoku = Gomoku("localhost", 1234, True)

ret = my_gomoku.connect()
if ret: # success connect
    pass
else:   # fail connect
    pass

# 모든 명령은 위와 같이 ret을 이용하여 성공 실패 유무 확인 가능

ret = my_gomoku.ready() # 준비
ret = my_gomoku.ready(True) # 준비 취소

ret_tuple = my_gomoku.update_or_end() # update 또는 end 신호를 수신하는 메소드
success, command, turn, data = ret_tuple    # bool, int, int, bytes 형태, 맨 첫 변수는 성공 실패 유무
if command == 2: # update 명령
    pass
if command == 4: # end 명령
    pass

# 각 명령별 turn, data는 문서 참고

x = 8
y = 7
ret = my_gomoku.put(x, y) # (x,y) 좌표에 돌 두기 -> 데이터 전송

# 돌 색상 처리는 서버에서 처리해 줄 예정

