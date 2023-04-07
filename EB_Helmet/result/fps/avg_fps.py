with open('./result/fps/fps.txt', 'r') as fps_file:
    fps = 0.00
    num = 0
    for line in fps_file.readlines():
        fps = fps + float(line)
        num = num + 1

print('avg_fps:%.2f' % (fps / num))