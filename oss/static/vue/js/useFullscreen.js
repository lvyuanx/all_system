const { ref, onMounted, onUnmounted } = Vue;

export function useFullscreen(elRef) {
  const isFullscreen = ref(false);

  const enter = () => {
    const el = elRef?.value || document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen();
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen();
    } else if (el.msRequestFullscreen) {
      el.msRequestFullscreen();
    }
  };

  const exit = () => {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  };

  const toggle = () => {
    if (isFullscreen.value) {
      exit();
    } else {
      enter();
    }
  };

  const handleChange = () => {
    isFullscreen.value =
      !!document.fullscreenElement ||
      !!document.webkitFullscreenElement ||
      !!document.msFullscreenElement;
  };

  onMounted(() => {
    document.addEventListener("fullscreenchange", handleChange);
    document.addEventListener("webkitfullscreenchange", handleChange);
    document.addEventListener("msfullscreenchange", handleChange);
  });

  onUnmounted(() => {
    document.removeEventListener("fullscreenchange", handleChange);
    document.removeEventListener("webkitfullscreenchange", handleChange);
    document.removeEventListener("msfullscreenchange", handleChange);
  });

  return { isFullscreen, enter, exit, toggle };
}
