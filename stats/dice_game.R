library(dplyr)
library(tidyr)
library(purrr)
library(ggplot2)
library(hrbrthemes)


# Config ------------------------------------------------------------------

cfg <-
  list(
    players_per_game = 1:5
    , games = 100
  )

# comment out if this doesn't work
theme_set(hrbrthemes::theme_ft_rc())


allplayers <- 
  tibble(
    player_id = 1:10 %>%
      as.factor()
  )

# Base model --------------------------------------------------------------

diceThrow <- function(players){
  1:6 %>% sample(players %>% length()) #%>%
    # case_when()>= a
}

game <-
  tibble(
    game_id = 1:cfg$games
    # game_id = 1
    , player_id = game_id %>%
      purrr::map(~allplayers$player_id %>% sample(cfg$players_per_game %>% sample(1)))
    , players_n = player_id %>% purrr::map_int(length)
    , bot = game_id %>%
      purrr::map_int(~1:6 %>% sample(1))
    , base_reward = 10 # game_id %>% 
  ) %>%
  mutate(
    throw = player_id %>% purrr::map(diceThrow)
    , win = bot %>%
      purrr::map2(throw, ~.y >= .x)
    , loss = bot %>%
      purrr::map2(throw, ~.y < .x)
  )

# Game stats --------------------------------------------------------------

game <-
  game %>%
  tidyr::unnest(c(player_id, throw, win, loss)) %>%
  # tidyr::unnest_legacy(player_id, throw, win, loss) %>%
  # complete(game_id, nesting(player_id)) %>%
  # group_by(game_id) %>%
  # fill(players_n:base_reward, .direction = "downup")
  # select(player_id, win:loss) %>% ftable()
  group_by(player_id) %>%
  mutate(
    win_streak =
      case_when(
        loss ~ NA_integer_
        , win ~ 1L
      )
    , loss_streak =
      case_when(
        loss ~ 1L
        , win ~ NA_integer_
      )
  ) %>% 
  mutate_at(
    vars(win_streak:loss_streak)
    # TODO demistify
    # this simply does a "partial" cumsum, resetting at every NA
    # https://r.789695.n4.nabble.com/partial-cumsum-td899789.html
    , ~ ave(., rev(cumsum(rev(is.na(.)))), FUN=cumsum) 
  )

# View(game)

# Visualize game stats ----------------------------------------------------

game %>%
  pivot_longer(cols = throw:loss_streak) %>%
  # gather("name", "value", throw, win, loss, win_streak, loss_streak) %>%
  qplot(
    game_id
    , value
    , data = .
    , color = player_id
    , geom = "point"
    , alpha = 0.5
  ) +
  # geom_line() +
  facet_wrap(vars(name))

# players with at least 1 win
allplayers <-
  allplayers %>%
  left_join(
    game %>%
      filter(win) %>%
      distinct(player_id, win) #%>%
      # head(2)
  )

# Reward formula ----------------------------------------------------------

game <-
  game %>%
  mutate(
    # FIXME per game, total wins, players who won?
    total_winners = allplayers %>%
      filter(win) %>% count() %>% first()
    , reward = as.integer(
      # FIXME total per game, or all games?
      # number_of_participants  
      players_n *
      (base_reward /
       # FIXME per game, total wins, players who won?
         total_winners
       ) *
      (win_streak))
  )

game %>%
  qplot(
    game_id
    , reward
    , data = .
    , color = player_id
    , geom = c("point", "line")
  ) +
  geom_line()

