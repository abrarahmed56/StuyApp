<?php
   echo "Hi";
   if ( isset($_GET['submit']) ) {
      echo "Hi again";
      $targ_w = $targ_h = 500;
      $jpeg_quality = 90;

      $src = $_GET['source'];
      $img_r = imagecreatefromjpeg($src);
      $dst_r = ImageCreateTrueColor( $targ_w, $targ_h );

      imagecopyresampled($dst_r,$img_r,0,0,$_GET['x'],$_GET['y'],
      $targ_w,$targ_h,$_GET['w'],$_GET['h']);

      //header('Content-type: image/jpeg');
      imagejpeg($dst_r, 'images/tst.jpg', $jpeg_quality);
      if (is_writable('images/tst.jpg')) {
      	 echo "writable";
      } else {
      	echo "unwritable";
      }
   }
?>
<html>
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
<script type=text/javascript src="../static/jquery.Jcrop.js"></script>

		<script language="Javascript">

			$(function(){

				$('#target').Jcrop({
					aspectRatio: 1,
					onSelect: updateCoords
				});

			});

			function updateCoords(c)
			{
				$('#x').val(c.x);
				$('#y').val(c.y);
				$('#w').val(c.w);
				$('#h').val(c.h);
			};

			function checkCoords()
			{
				if (parseInt($('#w').val())) return true;
				alert('Please select a crop region then press submit.');
				return false;
			};

		</script>
Please crop your schedule, starting with the class on the upper left side
<img id="target" src="../blah/scheduleforfinalproject.jpg" alt="Image">
<form method="GET" onsubmit="return checkCoords();" enctype="multipart/form-data">
<input type="hidden" id="x" name="x"></input>
<input type="hidden" id="y" name="y"></input>
<input type="hidden" id="w" name="w"></input>
<input type="hidden" id="h" name="h"></input>
<input type="submit" name="submit" value="Crop Image"></submit>
</form>
</html>
