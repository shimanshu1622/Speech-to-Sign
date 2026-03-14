import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#10b981"
    },
    secondary: {
      main: "#0f172a"
    },
    background: {
      default: "#0a1014",
      paper: "#111827"
    }
  },
  typography: {
    fontFamily: "Inter, Roboto, sans-serif"
  }
});

export default theme;