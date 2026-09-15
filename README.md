# youwebd-assets

유웹디 홈페이지(아임웹)에서 쓰는 이미지·동영상·폰트입니다.

- hero/: 메인 히어로 카드 13곳 (png 정지 화면, mp4 10초 무음) + 로고
- kit/: 섹션별 통합 코드 킷(youwebd-imweb-section-kit)의 제작 사례 목업 8장
- fonts/: 섹션별 통합 코드 킷 전용 서체(YWD Clash Display). 37개 위젯 파일이 전부 같은 폰트를 base64 로
  각자 품고 있어서(자기완결 원칙), 파일 하나만 있어도 여기 CDN 주소로 받아 쓰면 여러 위젯을 한 페이지에
  모아도 폰트가 한 번만 내려받아집니다.
- 주소 형식: https://cdn.jsdelivr.net/gh/youwebd/youwebd-assets@main/폴더명/파일명
