import { useState, useRef, useEffect } from "react";
import {
  Box,
  Typography,
  IconButton,
  Paper,
  TextField,
  Avatar,
  Button,
  CircularProgress,
  Chip,
  Stack
} from "@mui/material";

import MicIcon from "@mui/icons-material/Mic";
import StopIcon from "@mui/icons-material/Stop";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";

export default function LiveSTT() {
  const [recording, setRecording] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isConnecting, setIsConnecting] = useState(false);

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const workletNodeRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const chatWindowRef = useRef(null);

  const messageId = useRef(0);
  const pollingIntervals = useRef({});

  const addMessage = (sender, text) => {
    setMessages((prev) => [
      ...prev,
      {
        id: messageId.current++,
        sender,
        text,
        timestamp: new Date(),
        isTranslating: false,
        videoUrl: null,
        skeletonUrl: null,
        glosses: null
      }
    ]);
  };

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop =
        chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  // cleanup
  useEffect(() => {
    return () => {
      Object.values(pollingIntervals.current).forEach(clearInterval);
    };
  }, []);

  const startRecording = async () => {
    setIsConnecting(true);
    addMessage("system", "Connecting microphone...");

    wsRef.current = new WebSocket("ws://127.0.0.1:8000/ws/transcribe");

    wsRef.current.onopen = () => {
      addMessage("system", "Listening...");
      setRecording(true);
      setIsConnecting(false);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.text && data.text.trim()) {
        stopAudio();

        addMessage("user", data.text);
        setRecording(false);
      }
    };

    wsRef.current.onerror = () => {
      addMessage("system", "Connection error.");
      setRecording(false);
      setIsConnecting(false);
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      mediaStreamRef.current = stream;

      audioContextRef.current = new AudioContext({ sampleRate: 16000 });

      await audioContextRef.current.audioWorklet.addModule("/recorder-worklet.js");

      const source = audioContextRef.current.createMediaStreamSource(stream);

      workletNodeRef.current = new AudioWorkletNode(
        audioContextRef.current,
        "recorder-processor"
      );

      workletNodeRef.current.port.onmessage = (event) => {
        if (wsRef.current?.readyState === 1) {
          wsRef.current.send(event.data);
        }
      };

      source.connect(workletNodeRef.current).connect(audioContextRef.current.destination);
    } catch (err) {
      addMessage("system", "Microphone permission denied.");
      setIsConnecting(false);
    }
  };

  const stopAudio = () => {
    workletNodeRef.current?.disconnect();
    mediaStreamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();
  };

  const stopRecording = () => {
    if (wsRef.current?.readyState === 1) {
      wsRef.current.send(JSON.stringify({ text: "STOP" }));
    }

    stopAudio();
    setRecording(false);
  };

  // ======================================================
  // ASL GENERATION
  // ======================================================

  const generateASLVideo = async (messageId, text) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId ? { ...m, isTranslating: true } : m
      )
    );

    try {
      const res = await fetch("http://127.0.0.1:8000/jobs/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      const data = await res.json();
      const jobId = data.job_id;

      const interval = setInterval(async () => {
        const poll = await fetch(`http://127.0.0.1:8000/jobs/${jobId}`);
        const pollData = await poll.json();

        if (pollData.status === "DONE") {
          clearInterval(interval);

          setMessages((prev) =>
            prev.map((m) =>
              m.id === messageId
                ? {
                    ...m,
                    isTranslating: false,
                    videoUrl: pollData.result.video,
                    skeletonUrl: pollData.result.skeleton,
                    glosses: pollData.result.glosses
                  }
                : m
            )
          );
        }
      }, 2000);

      pollingIntervals.current[jobId] = interval;
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      height="100%"
      bgcolor="background.paper"
    >
      {/* CHAT WINDOW */}

      <Box
        ref={chatWindowRef}
        flex={1}
        p={3}
        sx={{ overflowY: "auto" }}
      >
        {messages.map((msg) => {
          const isUser = msg.sender === "user";

          return (
            <Box
              key={msg.id}
              display="flex"
              justifyContent={isUser ? "flex-end" : "flex-start"}
              mb={2}
            >
              {!isUser && (
                <Avatar sx={{ mr: 1 }}>
                  <SmartToyIcon />
                </Avatar>
              )}

              <Paper
                sx={{
                  p: 2,
                  maxWidth: 420,
                  bgcolor: isUser ? "primary.main" : "grey.900",
                  color: "white"
                }}
              >
                <Typography>{msg.text}</Typography>

                {isUser && (
                  <Box mt={2}>
                    {msg.videoUrl ? (
                      <Box>
                        {/* GLOSS TOKENS */}

                        {msg.glosses && (
                          <Stack direction="row" spacing={1} flexWrap="wrap" mb={1}>
                            {msg.glosses.map((g, i) => (
                              <Chip
                                key={i}
                                label={g}
                                size="small"
                                color="success"
                              />
                            ))}
                          </Stack>
                        )}

                        {/* VIDEO PLAYERS */}

                        <Stack direction="row" spacing={2}>
                          <video src={msg.videoUrl} controls width="180" />
                          <video src={msg.skeletonUrl} controls width="180" />
                        </Stack>
                      </Box>
                    ) : msg.isTranslating ? (
                      <Box mt={2} textAlign="center">
                        <CircularProgress size={20} />
                        <Typography variant="caption">
                          Generating sign animation...
                        </Typography>
                      </Box>
                    ) : (
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => generateASLVideo(msg.id, msg.text)}
                        sx={{ mt: 1 }}
                      >
                        Generate ASL
                      </Button>
                    )}
                  </Box>
                )}
              </Paper>

              {isUser && (
                <Avatar sx={{ ml: 1 }}>
                  <PersonIcon />
                </Avatar>
              )}
            </Box>
          );
        })}
      </Box>

      {/* INPUT BAR */}

      <Box
        p={2}
        display="flex"
        gap={2}
        alignItems="center"
        borderTop="1px solid #222"
      >
        <TextField
          fullWidth
          disabled
          placeholder={recording ? "Listening..." : "Click mic to speak"}
        />

        <IconButton
          color={recording ? "error" : "primary"}
          onClick={recording ? stopRecording : startRecording}
        >
          {isConnecting ? (
            <CircularProgress size={24} />
          ) : recording ? (
            <StopIcon />
          ) : (
            <MicIcon />
          )}
        </IconButton>
      </Box>
    </Box>
  );
}