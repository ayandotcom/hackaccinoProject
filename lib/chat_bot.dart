// import 'dart:developer';
// import 'package:flutter/material.dart';
// import 'package:http/http.dart' as http;
// import 'dart:convert';

// class ChatbotWidget extends StatefulWidget {
//   @override
//   _ChatbotWidgetState createState() => _ChatbotWidgetState();
// }

// class _ChatbotWidgetState extends State<ChatbotWidget> {
//   final TextEditingController _inputController = TextEditingController();
//   List<Map<String, String>> _messages = [];
//   String _stage = 'goal'; // Track the current stage (goal, height, weight)
//   String? _goal, _height, _weight;

//   Future<void> _sendData() async {
//     final input = _inputController.text;

//     // Handle conversation stages
//     if (_stage == 'goal') {
//       setState(() {
//         _messages.add({'sender': 'user', 'text': input});
//         _goal = input;
//       });

//       await _showTypingIndicator();
//       setState(() {
//         _messages.add({'sender': 'bot', 'text': 'What is your height (cm)?'});
//       });
//       _stage = 'height';
//     } else if (_stage == 'height') {
//       setState(() {
//         _messages.add({'sender': 'user', 'text': 'Height: $input cm'});
//         _height = input;
//       });

//       await _showTypingIndicator();
//       setState(() {
//         _messages.add({'sender': 'bot', 'text': 'What is your weight (kg)?'});
//       });
//       _stage = 'weight';
//     } else if (_stage == 'weight') {
//       setState(() {
//         _messages.add({'sender': 'user', 'text': 'Weight: $input kg'});
//         _weight = input;
//       });

//       await _showTypingIndicator();
//       setState(() {
//         _messages.add({'sender': 'bot', 'text': 'This is the plan I have generated.'});
//       });

//       // Send data to server after collecting all inputs
//       final response = await http.post(
//         Uri.parse('http://127.0.0.1:5000/chatbot'), // Your Flask API URL
//         headers: {'Content-Type': 'application/json'},
//         body: json.encode({
//           'height': _height,
//           'weight': _weight,
//           'query': _goal,
//         }),
//       );

//       if (response.statusCode == 200) {
//         await _showTypingIndicator();
//         final botResponse = json.decode(response.body)['plan'].toString();
//         setState(() {
//           _messages.add({'sender': 'bot', 'text': botResponse});
//         });
//       } else {
//         await _showTypingIndicator();
//         setState(() {
//           _messages.add({'sender': 'bot', 'text': "Error: ${response.statusCode}"});
//         });
//       }

//       _stage = 'goal'; // Reset the conversation for future use
//     }

//     _inputController.clear(); // Clear input field after sending
//   }

//   // Show a "typing" indicator with 3 dots before displaying each bot message
//   Future<void> _showTypingIndicator() async {
//     setState(() {
//       _messages.add({'sender': 'bot', 'text': '...'});
//     });
//     await Future.delayed(Duration(seconds: 1)); // Simulate loading time
//     setState(() {
//       _messages.removeWhere((message) => message['text'] == '...'); // Remove "typing" indicator
//     });
//   }

//   @override
//   void initState() {
//     super.initState();
//     _messages.add({'sender': 'bot', 'text': 'Welcome! How may I help you?'}); // Initial bot message
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: Text('Fitness Chatbot'),
//         backgroundColor: Colors.teal,
//       ),
//       body: Padding(
//         padding: const EdgeInsets.all(16.0),
//         child: Column(
//           children: [
//             Expanded(
//               child: ListView.builder(
//                 itemCount: _messages.length,
//                 itemBuilder: (context, index) {
//                   final message = _messages[index];
//                   final isBot = message['sender'] == 'bot';
//                   return Container(
//                     margin: EdgeInsets.symmetric(vertical: 5),
//                     alignment: isBot ? Alignment.centerLeft : Alignment.centerRight,
//                     child: Container(
//                       padding: EdgeInsets.all(10),
//                       decoration: BoxDecoration(
//                         color: isBot ? Colors.grey[300] : Colors.blue[300],
//                         borderRadius: BorderRadius.circular(10),
//                       ),
//                       child: Text(
//                         message['text']!,
//                         style: TextStyle(color: isBot ? Colors.black : Colors.white),
//                       ),
//                     ),
//                   );
//                 },
//               ),
//             ),
//             Row(
//               children: [
//                 Expanded(
//                   child: TextField(
//                     controller: _inputController,
//                     decoration: InputDecoration(
//                       labelText: 'Type your response...',
//                       border: OutlineInputBorder(),
//                     ),
//                   ),
//                 ),
//                 IconButton(
//                   icon: Icon(Icons.send),
//                   onPressed: _sendData,
//                 ),
//               ],
//             ),
//           ],
//         ),
//       ),
//     );
//   }
// }

import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ChatbotWidget extends StatefulWidget {
  @override
  _ChatbotWidgetState createState() => _ChatbotWidgetState();
}

class _ChatbotWidgetState extends State<ChatbotWidget> {
  final TextEditingController _inputController = TextEditingController();
  List<Map<String, String>> _messages = [];
  String _stage = 'goal'; // Track the current stage (goal, height, weight)
  String? _goal, _height, _weight;

  Future<void> _sendData() async {
    final input = _inputController.text;

    if (_stage == 'goal') {
      setState(() {
        _messages.add({'sender': 'user', 'text': input});
        _goal = input;
      });

      await _showTypingIndicator();
      setState(() {
        _messages.add({'sender': 'bot', 'text': 'What is your height (cm)?'});
      });
      _stage = 'height';
    } else if (_stage == 'height') {
      setState(() {
        _messages.add({'sender': 'user', 'text': 'Height: $input cm'});
        _height = input;
      });

      await _showTypingIndicator();
      setState(() {
        _messages.add({'sender': 'bot', 'text': 'What is your weight (kg)?'});
      });
      _stage = 'weight';
    } else if (_stage == 'weight') {
      setState(() {
        _messages.add({'sender': 'user', 'text': 'Weight: $input kg'});
        _weight = input;
      });

      await _showTypingIndicator();
      setState(() {
        _messages.add({'sender': 'bot', 'text': 'This is the plan I have generated.'});
      });

      final response = await http.post(
        Uri.parse('http://10.81.32.74:5000/chatbot'), // Your Flask API URL 127.0.0.1
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'height': _height, 'weight': _weight, 'query': _goal}),
      );

      if (response.statusCode == 200) {
        await _showTypingIndicator();
        final botResponse = json.decode(response.body)['plan'].toString();
        setState(() {
          _messages.add({'sender': 'bot', 'text': botResponse});
        });
      } else {
        await _showTypingIndicator();
        setState(() {
          _messages.add({'sender': 'bot', 'text': "Error: ${response.statusCode}"});
        });
      }

      _stage = 'goal'; // Reset for future conversation
    }

    _inputController.clear(); // Clear input field
  }

  Future<void> _showTypingIndicator() async {
    setState(() {
      _messages.add({'sender': 'bot', 'text': '...'});
    });
    await Future.delayed(Duration(seconds: 1)); // Simulate loading
    setState(() {
      _messages.removeWhere((message) => message['text'] == '...');
    });
  }

  @override
  void initState() {
    super.initState();
    _messages.add({'sender': 'bot', 'text': 'Welcome! How may I help you?'});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        flexibleSpace: Center(
        child: Text(
          'FITBUDDY',
           style: TextStyle(
            color: Colors.white,
            letterSpacing: 1.5,
            fontWeight: FontWeight.w600, 
            fontSize: 28,
            ),
        ),
      ),
        backgroundColor: Color(0xFF006400),
      ),
      body: Container(
        color: Colors.black, // Background color for the body
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final message = _messages[index];
                  final isBot = message['sender'] == 'bot';
                  return Container(
                    margin: EdgeInsets.symmetric(vertical: 5),
                    alignment: isBot ? Alignment.centerLeft : Alignment.centerRight,
                    child: Container(
                      padding: EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isBot ? Colors.grey[800] : Colors.teal[300],
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        message['text']!,
                        style: TextStyle(
                          color: isBot ? Colors.white : Colors.black, // Adjust text color
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputController,
                    style: TextStyle(color: Colors.white), // Input text color
                    decoration: InputDecoration(
                      labelText: 'Type your response...',
                      labelStyle: TextStyle(color: Colors.white54), // Label color
                      border: OutlineInputBorder(
                        borderSide: BorderSide(color: Colors.white), // Border color
                      ),
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.send, color: Colors.green), // Send icon color
                  onPressed: _sendData,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
