import { Box, Typography, Avatar } from "@mui/material";

export default function ChatMessage({ sender, text }) {
  const isUser = sender === "user";

  return (
    <Box
      display="flex"
      justifyContent={isUser ? "flex-end" : "flex-start"}
      mb={2}
    >
      {!isUser && <Avatar sx={{ mr: 1 }}>A</Avatar>}

      <Box
        sx={{
          bgcolor: isUser ? "primary.main" : "grey.800",
          color: "white",
          px: 2,
          py: 1,
          borderRadius: 2,
          maxWidth: "70%"
        }}
      >
        <Typography variant="body2">{text}</Typography>
      </Box>
    </Box>
  );
}