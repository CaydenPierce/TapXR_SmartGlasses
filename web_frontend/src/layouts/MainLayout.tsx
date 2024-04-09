import {
  Flex,
  Stack,
  ActionIcon,
  rem,
  Container,
  ContainerProps,
  FlexProps,
  createPolymorphicComponent,
  createStyles,
  Box,
  Image,
  Transition,
} from "@mantine/core";
import {
  IconLayoutSidebarRightCollapse,
  IconLayoutSidebarRightExpand,
} from "@tabler/icons-react";
import { motion } from "framer-motion";
import { GAP_VH } from "../components/CardWrapper";
import ExplorePane from "../components/ExplorePane";
import SettingsModal from "../components/SettingsModal";
import Sidebar from "../components/Sidebar";
import { useRecoilValue, useSetRecoilState } from "recoil";
import {
  entitiesState,
  isExplicitListeningState,
  selectedCardIdState,
  //showExplorePaneValue,
} from "../recoil";
import { useDisclosure, useMediaQuery } from "@mantine/hooks";
import { useState } from "react";
import { setUserIdAndDeviceId } from "../utils/utils";
import CardScrollArea from "../components/CardScrollArea";

// animate-able components for framer-motion
// https://github.com/orgs/mantinedev/discussions/1169#discussioncomment-5444975
const PFlex = createPolymorphicComponent<"div", FlexProps>(Flex);
const PContainer = createPolymorphicComponent<"div", ContainerProps>(Container);

const useStyles = createStyles({
  root: {
    height: "100vh",
    width: "100vw",
    background:
      "var(--bg-gradient-full---blue, linear-gradient(180deg, #191A27 2.23%, #14141D 25.74%, #14141D 49.42%, #14141D 73.62%, #14141D 96.28%))",
    overflow: "clip",
  },

  container: {
    width: "100%",
    maxWidth: "auto",
    height: "100%",
    padding: 0,
    //flex: "1 1 0",
  },
});

const MainLayout = () => {
  const { classes } = useStyles();

  const entities = useRecoilValue(entitiesState);
  const isExplicitListening = useRecoilValue(isExplicitListeningState);
  //const showExplorePane = useRecoilValue(showExplorePaneValue);
  const showExplorePane = true;
  const setSelectedCardId = useSetRecoilState(selectedCardIdState);
  const [loadingViewMore, setLoadingViewMore] = useState(false);

  const [opened, { open: openSettings, close: closeSettings }] =
    useDisclosure(false);
  const smallerThanMedium = useMediaQuery("(max-width: 62em)");

  const toggleSettings = () => {
    if (opened) {
      closeSettings();
    } else {
      openSettings();
    }
  };

  return (
    <>
      <PFlex component={motion.div} className={classes.root} layout>
        <Sidebar settingsOpened={opened} toggleSettings={toggleSettings} />
        <PContainer
          component={motion.div}
          layout
          fluid
          className={classes.container}
          //w={showExplorePane ? "50%" : "100%"}
          w={"40%"}
          pt={`${GAP_VH}vh`}
          px={"1rem"}
          transition={{ bounce: 0 }}
          mx={"0px"}
        >
          {entities.length === 0 && !isExplicitListening && (
            <Box w="50%" mx="auto" mt="xl">
              <Image src={"/blobs.gif"} fit="cover" />
            </Box>
          )}
          {/* Left Panel */}
          <CardScrollArea />
        </PContainer>

        <PContainer
          component={motion.div}
          layout
          mx={"0px"}
//          sx={{
//            flex: showExplorePane ? "1 1 0" : "0",
//          }}
          className={classes.container}
            sx={{
            maxWidth: "none", // Disables max-width
            // Add more styles here as needed
          }}
        >
        <Flex mx={"0px"} sx={{ height: "100%", maxWidth: "auto"}}>
            {entities.length > 0 && (
              <Stack align="center" w="3rem">
                <ActionIcon
                  onClick={() => {
                    setSelectedCardId((prevState) =>
                      prevState === undefined
                        ? entities.at(-1)?.uuid
                        : undefined
                    );
                  }}
                  size={rem(5)}
                  mt="sm"
                  disabled={entities.at(-1)?.url === undefined}
                >
                  {showExplorePane ? (
                    <IconLayoutSidebarRightCollapse />
                  ) : (
                    <IconLayoutSidebarRightExpand />
                  )}
                </ActionIcon>
              </Stack>
            )}
            <Transition
              mounted={showExplorePane}
              transition="slide-left"
              duration={400}
              timingFunction="ease"
            >
              {(styles) => (
                <motion.div
                  style={{ ...styles, height: "100%", width: "100%" }}
                >
                  <ExplorePane
                    loading={loadingViewMore}
                    setLoading={setLoadingViewMore}
                  />
                </motion.div>
              )}
            </Transition>
          </Flex>
        </PContainer>
      </PFlex>

      <SettingsModal
        smallerThanMedium={smallerThanMedium}
        opened={opened}
        closeSettings={closeSettings}
        setUserIdAndDeviceId={setUserIdAndDeviceId}
      />
    </>
  );
};

export default MainLayout;
