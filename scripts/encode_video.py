"""Encode and decode-validate the entire frame sequence; create visual QA artifacts."""
import pathlib,sys,json,subprocess,datetime,re
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/python'))
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
ff=imageio_ffmpeg.get_ffmpeg_exe();out=R/'output';frames=sorted((out/'frames').glob('*.png'))
assert len(frames)==432, f'Expected 432 rendered frames, found {len(frames)}'
for i,f in enumerate(frames,1):assert f.stem==f'{i:04}',f'Missing frame {i}'
command=[ff,'-y','-framerate','24','-start_number','1','-i',str(out/'frames/%04d.png'),'-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(out/'taichi_final.mp4')]
subprocess.run(command,check=True)
check=subprocess.run([ff,'-v','error','-i',str(out/'taichi_final.mp4'),'-f','null','-'],capture_output=True,text=True,check=True)
assert not check.stderr.strip(),check.stderr
reader=imageio_ffmpeg.read_frames(str(out/'taichi_final.mp4'),pix_fmt='rgb24');meta=next(reader);count=sum(1 for _ in reader)
report={'width':meta['size'][0],'height':meta['size'][1],'fps':meta['fps'],'duration':meta['duration'],'frames':count,'codec':meta.get('codec'),'bytes':(out/'taichi_final.mp4').stat().st_size,'validation':'All 432 frames decoded successfully; no FFmpeg errors','audio':False}
assert count==432 and meta['size']==(1920,1080),report
(out/'video_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
Image.open(out/'frames/0172.png').save(out/'poster.jpg',quality=94)
sheet=Image.new('RGB',(1440,600),(16,22,25));draw=ImageDraw.Draw(sheet)
for i,frame in enumerate([1,86,172,258,344,432]):
    img=Image.open(out/f'frames/{frame:04}.png');img.thumbnail((480,270));x=(i%3)*480;y=(i//3)*300;sheet.paste(img,(x,y));draw.text((x+12,y+278),f'{(frame-1)/24:05.2f}s  /  FRAME {frame:03}',fill=(174,198,191))
sheet.save(out/'contact_sheet.jpg',quality=94)
row={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'07_delivery','event':'video_validated','status':'SUCCEEDED','progress':100,**report}
with (R/'logs/events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
print(json.dumps(report,indent=2))
