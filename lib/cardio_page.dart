import 'package:flutter/material.dart';
import 'package:youtube_player_iframe/youtube_player_iframe.dart';
import 'dart:ui_web' as ui_web;
import 'dart:convert';
import 'services/auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:async';

class CardioPage extends StatefulWidget {
  @override
  _CardioPageState createState() => _CardioPageState();
}

class _CardioPageState extends State<CardioPage> {
  final _controller = YoutubePlayerController();
  final _authService = AuthService();
  bool _isLoading = false;
  String _errorMessage = '';
  String _exerciseCount = '';
  String _formFeedback = '';
  Timer? _exerciseTimer;
  bool _isExercising = false;

  // Video IDs
  final List<String> videoIds = ["XPU9K9QM7ME", "auBLPXO8Fww", "L8fvypPrzzs", "S7HEm-fd534"];
  int currentVideoIndex = 0;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      await _controller.loadVideoById(videoId: videoIds[currentVideoIndex]);
    } catch (e) {
      _setError('Failed to load video: $e');
    }
  }

  void _setError(String message) {
    setState(() {
      _errorMessage = message;
    });
  }

  void _clearError() {
    setState(() {
      _errorMessage = '';
    });
  }

  Future<void> _startVideo() async {
    _clearError();
    setState(() {
      _isLoading = true;
      _isExercising = true;
    });

    try {
      await _controller.playVideo();
      await _sendStartWorkoutRequest();
      _startExerciseTracking();
    } catch (e) {
      _setError('Failed to start workout: $e');
      _isExercising = false;
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _stopVideo() {
    _controller.pauseVideo();
    _stopExerciseTracking();
    setState(() {
      _isExercising = false;
    });
  }

  void _startExerciseTracking() {
    _exerciseTimer?.cancel();
    _exerciseTimer = Timer.periodic(Duration(seconds: 1), (timer) async {
      if (!_isExercising) {
        timer.cancel();
        return;
      }
      await _updateExerciseStatus();
    });
  }

  void _stopExerciseTracking() {
    _exerciseTimer?.cancel();
    _exerciseTimer = null;
  }

  Future<void> _updateExerciseStatus() async {
    try {
      final response = await http.get(Uri.parse('http://localhost:5001/status'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _exerciseCount = data['count'].toString();
          _formFeedback = data['feedback'] ?? '';
        });
      }
    } catch (e) {
      print('Error updating exercise status: $e');
    }
  }

  Future<void> _nextVideo() async {
    if (currentVideoIndex < videoIds.length - 1) {
      setState(() {
        currentVideoIndex++;
      });
      await _initializeVideo();
    } else {
      _showWorkoutCompletedDialog();
    }
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,  // Prevent dismissing by tapping outside
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed this exercise.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();  // Pop the dialog
                Navigator.of(context).maybePop();  // Safely try to pop the page
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _sendStartWorkoutRequest() async {
    try {
      final response = await http.get(Uri.parse('http://localhost:5001/jumpingjacks'));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('Workout started successfully: ${data['data']}');
      } else if (response.statusCode == 401) {
        // Handle authentication error
        _setError('Authentication required. Please log in again.');
        Navigator.pushReplacementNamed(context, '/login');
      } else if (response.statusCode == 429) {
        _setError('Rate limit exceeded. Please try again later.');
      } else {
        _setError('Failed to start workout: ${response.body}');
      }
    } catch (e) {
      if (e.toString().contains('Authentication required')) {
        Navigator.pushReplacementNamed(context, '/login');
      } else {
        _setError('Error sending request: $e');
      }
    }
  }

  @override
  void dispose() {
    _exerciseTimer?.cancel();
    _controller.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Cardio Workouts'),
        backgroundColor: Colors.black,
      ),
      body: Container(
        color: Colors.black,
        child: Column(
          children: [
            if (_errorMessage.isNotEmpty)
              Padding(
                padding: const EdgeInsets.all(8.0),
                child: Text(
                  _errorMessage,
                  style: TextStyle(color: Colors.red),
                ),
              ),
            Expanded(
              child: Row(
                children: [
                  // Tutorial video
                  Expanded(
                    child: Container(
                      child: YoutubePlayer(
                        controller: _controller,
                        aspectRatio: 16 / 9,
                      ),
                    ),
                  ),
                  // Camera feed and exercise info
                  if (_isExercising)
                    Expanded(
                      child: Container(
                        padding: EdgeInsets.all(16),
                        child: Column(
                          children: [
                            // Camera feed
                            Expanded(
                              child: Container(
                                decoration: BoxDecoration(
                                  border: Border.all(color: Colors.white),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: Image.network(
                                    'http://localhost:5001/video_feed',
                                    fit: BoxFit.contain,
                                    loadingBuilder: (context, child, progress) {
                                      if (progress == null) return child;
                                      return Center(
                                        child: CircularProgressIndicator(),
                                      );
                                    },
                                    errorBuilder: (context, error, stackTrace) {
                                      return Center(
                                        child: Text(
                                          'Camera feed unavailable',
                                          style: TextStyle(color: Colors.white),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ),
                            ),
                            SizedBox(height: 16),
                            // Exercise counter and feedback
                            Container(
                              padding: EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white10,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                children: [
                                  Text(
                                    'Reps: $_exerciseCount',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 24,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  if (_formFeedback.isNotEmpty)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 8.0),
                                      child: Text(
                                        _formFeedback,
                                        style: TextStyle(
                                          color: Colors.white70,
                                          fontSize: 16,
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
            SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: _isLoading ? null : _startVideo,
                  child: _isLoading
                      ? CircularProgressIndicator()
                      : Text('Start'),
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
