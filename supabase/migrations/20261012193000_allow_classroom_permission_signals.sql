-- Allow the classroom signaling messages used by the web room and standalone APK.
-- Keep existing signaling types and add the permission events used by the client.
ALTER TABLE public.online_class_signals
  DROP CONSTRAINT IF EXISTS online_class_signals_signal_type_check;

ALTER TABLE public.online_class_signals
  ADD CONSTRAINT online_class_signals_signal_type_check
  CHECK (
    signal_type = ANY (ARRAY[
      'join'::text,
      'leave'::text,
      'offer'::text,
      'answer'::text,
      'candidate'::text,
      'chat'::text,
      'board'::text,
      'media_permission'::text,
      'presence'::text,
      'draw_permission'::text,
      'tools_permission'::text,
      'camera_request'::text
    ])
  );
