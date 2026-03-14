import { Container, Typography, Box, Paper } from "@mui/material";
import LiveSTT from "./components/LiveSTT";

function App() {
  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      
      <Box textAlign="center" mb={3}>
        <Typography variant="h3" fontWeight="bold" color="primary">
          GenASL
        </Typography>

        <Typography variant="body2" color="text.secondary">
          Real-time Speech to Sign Language
        </Typography>
      </Box>

      <Paper
        elevation={6}
        sx={{
          height: "75vh",
          borderRadius: 4,
          overflow: "hidden"
        }}
      >
        <LiveSTT />
      </Paper>

    </Container>
  );
}

export default App;