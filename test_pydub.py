from pydub import AudioSegment


def joinVoice():
    file1_name = "mp3/01SLO0H0GC89PCVV380J42LAES07NDF4_2021-06-01_00-58-00_zhouxinglei%40tuhu.cn_015264292037_60116801_000103195c87a480-00A2020B-10499681-00000001.mp3"
    file2_name = "mp3/01SLO0H0GC89PCVV380J42LAES07NDF4_2021-06-01_00-58-48_zhangyanan%40tuhu.cn_015264292037_60116801_000103195c87a480-00A1020B-1049988C-00000001.mp3"
    # 加载需要拼接的两个文件
    sound1 = AudioSegment.from_mp3(file1_name)
    sound2 = AudioSegment.from_mp3(file2_name)
    # 取得两个文件的声音分贝
    db1 = sound1.dBFS
    db2 = sound2.dBFS
    dbplus = db1 - db2
    # 声音大小
    if dbplus < 0:
        sound1 += abs(dbplus)
    else:
        sound2 += abs(dbplus)
    # 拼接两个音频文件
    new_sound = sound1 + sound2
    save_name = "mp3/new.mp3"
    new_sound.export(save_name, format="mp3")
    return True


if __name__ == "__main__":
    joinVoice()