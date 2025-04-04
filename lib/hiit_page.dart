
import 'package:flutter/material.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';
import 'package:http/http.dart' as http;


class HIITPage extends StatefulWidget {
   @override
   _HIITPageState createState() => _HIITPageState();
 }


class _HIITPageState extends State<HIITPage> {
  final _controller = YoutubePlayerController();

  // Video IDs
  final List<String> videoIds = ["XPU9K9QM7ME","VtOYc6j5c", "vUnqwqqI", "op9kVnSso6Q", "hHdD5Ksdnmk", "_l3ySVKYVJ8"];
  int currentVideoIndex = 0;

  @override
  void initState() {
    super.initState();
    _controller.loadVideoById(videoId: videoIds[currentVideoIndex]);
  }

  void _startVideo() async {
    // Start the video first
    _controller.playVideo();

    // Then send the request to start the workout
    await _sendStartWorkoutRequest();
  }

  void _stopVideo() {
    _controller.pauseVideo();
  }

  void _nextVideo() {
    if (currentVideoIndex < videoIds.length - 1) {
      currentVideoIndex++;
    } else {
      _showWorkoutCompletedDialog();
      return; // Prevent loading the next video if workout is completed
    }
    _controller.loadVideoById(videoId: videoIds[currentVideoIndex]);
    // Don't start the video immediately here, wait for user to press start
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed this exercise.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context); // This will pop the dialog
                Navigator.pop(context); // This will pop the CardioPage and go back
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendStartWorkoutRequest() async {
    String url;
    if (currentVideoIndex == 0) {
      // For the first video (Pushups)
      url = 'http:// 10.81.32.74:5002/jumpingjacks'; // Replace with your Flask URL for pushups
    } else {
      // For the subsequent videos (Squats)
      url = 'http:// 10.81.32.74:5002/squats'; // Replace with your Flask URL for squats
    }

    try {
      final response = await http.post(Uri.parse(url));
      if (response.statusCode == 200) {
        // Handle the response if needed
        print('Workout started successfully: ${currentVideoIndex == 0 ? "Pushups" : "Squats"}');
      } else {
        // Handle the error
        print('Failed to start workout: ${response.body}');
      }
    } catch (error) {
      print('Error sending request: $error');
    }
  }

  @override
  void dispose() {
    _controller.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('High Interval Strength Training Workouts'),
      ),
      body: Center(
        child: Column(
          children: [
            Expanded(
              child: Container(
                width: 300,
                height: 200,
                child: YoutubePlayer(
                  controller: _controller,
                  aspectRatio: 16 / 9,
                ),
              ),
            ),
            SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: _startVideo,
                  child: Text('Start'),
                ),
                SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _stopVideo,
                  child: Text('Stop'),
                ),
                SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _nextVideo,
                  child: Text('Next'),
                ),
              ],
            ),
            SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

