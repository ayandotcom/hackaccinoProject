import 'package:flutter/material.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';

class FullWorkoutPage extends StatefulWidget {
  @override
  _FullWorkoutPageState createState() => _FullWorkoutPageState();
}

class _FullWorkoutPageState extends State<FullWorkoutPage> {
  String message = "You have to do 10 Pushups, 10 Squats, and 10 Planks";
  bool isWorkoutStarted = false;
  bool isLoading = false;
  String currentExercise = "";
  int exerciseCount = 0;
  String exerciseFeedback = "";
  Timer? _statusTimer;
  Timer? _videoTimer;
  Key _imageKey = UniqueKey();
  bool _isVideoError = false;

  @override
  void initState() {
    super.initState();
    _startWorkoutSequence();
    _startStatusUpdates();
    _startVideoFeedUpdates();
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    _videoTimer?.cancel();
    super.dispose();
  }

  void _startVideoFeedUpdates() {
    _videoTimer = Timer.periodic(Duration(milliseconds: 250), (timer) {
      if (mounted && !_isVideoError) {
        setState(() {
          _imageKey = UniqueKey();
        });
      }
    });
  }

  void _startStatusUpdates() {
    _statusTimer = Timer.periodic(Duration(milliseconds: 500), (timer) async {
      if (!mounted) return;
      
      try {
        final response = await http.get(Uri.parse('http://localhost:5001/status'));
        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          if (mounted) {
            setState(() {
              exerciseCount = data['count'] ?? 0;
              exerciseFeedback = data['feedback'] ?? '';
              _isVideoError = false;
            });
          }
        } else {
          throw Exception('Failed to fetch status');
        }
      } catch (e) {
        print('Error fetching status: $e');
        if (mounted) {
          setState(() {
            _isVideoError = true;
          });
        }
      }
    });
  }

  void _startWorkoutSequence() {
    Timer(Duration(seconds: 2), () {
      if (mounted) {
        setState(() {
          message = "Get ready to start your workout!";
        });
        Timer(Duration(seconds: 2), () {
          if (mounted) {
            setState(() {
              isWorkoutStarted = true;
              message = "Starting exercises...";
            });
            executeExercises();
          }
        });
      }
    });
  }

  Future<void> executeExercises() async {
    if (mounted) {
      setState(() {
        isLoading = true;
      });
    }

    try {
      // Pushups
      if (mounted) {
        setState(() {
          currentExercise = "Pushups";
          message = "Starting Pushups...";
        });
      }

      var response = await http.post(Uri.parse('http://localhost:5001/pushups'));
      var data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            message = "Doing Pushups: ${data['feedback'] ?? 'In progress...'}";
          });
        }
        await Future.delayed(Duration(seconds: 30));
      } else {
        if (mounted) {
          setState(() {
            message = "Error with Pushups: ${data['error'] ?? 'Unknown error'}";
          });
        }
        await Future.delayed(Duration(seconds: 2));
      }

      // Squats
      if (mounted) {
        setState(() {
          currentExercise = "Squats";
          message = "Starting Squats...";
        });
      }

      response = await http.post(Uri.parse('http://localhost:5001/squats'));
      data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            message = "Doing Squats: ${data['feedback'] ?? 'In progress...'}";
          });
        }
        await Future.delayed(Duration(seconds: 30));
      } else {
        if (mounted) {
          setState(() {
            message = "Error with Squats: ${data['error'] ?? 'Unknown error'}";
          });
        }
        await Future.delayed(Duration(seconds: 2));
      }

      // Plank
      if (mounted) {
        setState(() {
          currentExercise = "Plank";
          message = "Starting Plank...";
        });
      }

      response = await http.post(Uri.parse('http://localhost:5001/plank'));
      data = jsonDecode(response.body);
      
      if (response.statusCode == 200) {
        if (mounted) {
          setState(() {
            message = "Holding Plank: ${data['feedback'] ?? 'In progress...'}";
          });
        }
        await Future.delayed(Duration(seconds: 30));
      } else {
        if (mounted) {
          setState(() {
            message = "Error with Plank: ${data['error'] ?? 'Unknown error'}";
          });
        }
        await Future.delayed(Duration(seconds: 2));
      }

      // Workout completed
      if (mounted) {
        setState(() {
          message = "Workout completed!";
          currentExercise = "";
        });
      }
      
      _showWorkoutCompletedDialog();

    } catch (e) {
      if (mounted) {
        setState(() {
          message = "Error during workout: $e";
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  void _showWorkoutCompletedDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Workout Completed'),
          content: Text('Great job! You have completed all exercises.'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                Navigator.of(context).maybePop();
              },
              child: Text('Okay'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Full Workout'),
        backgroundColor: Theme.of(context).primaryColor,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Colors.blue.shade100,
              Colors.white,
            ],
          ),
        ),
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  height: MediaQuery.of(context).size.height * 0.4,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.grey.withOpacity(0.2),
                        spreadRadius: 2,
                        blurRadius: 8,
                        offset: Offset(0, 4),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Stack(
                      children: [
                        if (!_isVideoError)
                          Image.network(
                            'http://localhost:5001/video_feed?key=${DateTime.now().millisecondsSinceEpoch}',
                            key: _imageKey,
                            fit: BoxFit.contain,
                            loadingBuilder: (context, child, loadingProgress) {
                              if (loadingProgress == null) {
                                return child;
                              }
                              return Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    CircularProgressIndicator(),
                                    SizedBox(height: 16),
                                    Text(
                                      'Connecting to camera...',
                                      style: TextStyle(
                                        color: Colors.grey.shade700,
                                        fontSize: 16,
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            },
                            errorBuilder: (context, error, stackTrace) {
                              print('Video feed error: $error');
                              WidgetsBinding.instance.addPostFrameCallback((_) {
                                if (mounted) {
                                  setState(() {
                                    _isVideoError = true;
                                  });
                                }
                              });
                              return _buildErrorWidget();
                            },
                          )
                        else
                          _buildErrorWidget(),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 24),
                Card(
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      children: [
                        Text(
                          currentExercise.isEmpty ? 'Get Ready!' : currentExercise,
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            color: Theme.of(context).primaryColor,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        SizedBox(height: 12),
                        Text(
                          'Count: $exerciseCount',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.grey.shade800,
                          ),
                        ),
                        SizedBox(height: 12),
                        Text(
                          exerciseFeedback,
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: Colors.grey.shade600,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 24),
                if (!isWorkoutStarted)
                  ElevatedButton(
                    onPressed: () {
                      executeExercises();
                    },
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      backgroundColor: Theme.of(context).primaryColor,
                    ),
                    child: Text(
                      'Start Workout',
                      style: TextStyle(
                        fontSize: 18,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                if (isLoading)
                  Center(
                    child: CircularProgressIndicator(
                      color: Theme.of(context).primaryColor,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      color: Colors.grey.shade100,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.videocam_off, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'Camera feed unavailable',
              style: TextStyle(
                color: Colors.grey.shade700,
                fontSize: 16,
              ),
            ),
            SizedBox(height: 8),
            TextButton.icon(
              onPressed: () {
                setState(() {
                  _isVideoError = false;
                  _imageKey = UniqueKey();
                });
              },
              icon: Icon(Icons.refresh),
              label: Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

