(function init() {
  var socket = io()

  function reset_player() {
    let players = document.getElementsByClassName("player");
    for (let player_idx = 0; player_idx < players.length; player_idx++) {
      let player = players[player_idx];
      player.getElementById(`chips-text-player-${player_idx}`).innerHTML = 0;
      let card_backgrounds = player.getElementsByClassName("card-background");
      for (let card_background of card_backgrounds) {
        card_background.setAttribute("fill", "url(#card-back)");
      }
      let card_texts = player.getElementsByClassName("card-text");
      for (let card_text of card_texts) {
        card_text.innerHTML = "";
      }
    }
  }

  function reset_button() {
    let buttons = document.getElementsByClassName("button-background");
    for (let button of buttons) {
      button.setAttribute("fill", "transparent");
    }
  }

  function reset_community() {
    let community = document.getElementById("community");
    let card_backgrounds = community.getElementsByClassName("card-background");
    card_backgrounds[0].setAttribute("fill", "url(#card-back)");
    for (let i = 1; i < card_backgrounds.length; i++) {
      card_backgrounds[i].setAttribute("fill", "url(#card-blank)");
    }
    let card_texts = community.getElementsByClassName("card-text");
    card_texts[0].setAttribute("fill", "url(#card-back)");
    for (let i = 1; i < card_texts.length; i++) {
      card_texts[i].innerHTML = "";
    }
    community.getElementById("pot-text").innerHTML = 0;
  }

  function update_cards(config) {
    for (let player_idx = 0; player_idx < config["hole_cards"].length; player_idx++) {
      let cards = config["hole_cards"][player_idx];
      for (let card_idx = 0; card_idx < cards.length; card_idx++) {
        let card = document.getElementById(`card-player-${player_idx}-${card_idx}`);
        let card_string = cards[card_idx];
        update_card(card, card_string)
      }
    }
    let cards = config["community_cards"];
    for (let card_idx = 1; card_idx < cards.length; card_idx++) {
      let card = document.getElementById(`card-community-${card_idx}`);
      let card_string = cards[card_idx];
      update_card(card, card_string)
    }
  }

  function update_card(card, card_string) {
    let value = card_string[0];
    if (value == "T") {
      value = "10";
    }
    card.getElementsByClassName("card-text")[0].innerHTML = value;
    let suit = card_string[1];
    if (suit == "♣") {
      card.getElementsByClassName("card-background")[0].setAttribute("fill", "url(#card-club)");
      let card_text = card.getElementsByClassName("card-text")[0]
      card_text.setAttribute("stroke", "black");
      card_text.setAttribute("fill", "black");
    } else if (suit == "♠") {
      card.getElementsByClassName("card-background")[0].setAttribute("fill", "url(#card-spade)");
      let card_text = card.getElementsByClassName("card-text")[0]
      card_text.setAttribute("stroke", "black");
      card_text.setAttribute("fill", "black");
    } else if (suit == "♥") {
      card.getElementsByClassName("card-background")[0].setAttribute("fill", "url(#card-heart)");
      let card_text = card.getElementsByClassName("card-text")[0]
      card_text.setAttribute("stroke", "red");
      card_text.setAttribute("fill", "red");
    } else if (suit == "♦") {
      card.getElementsByClassName("card-background")[0].setAttribute("fill", "url(#card-diamond)");
      let card_text = card.getElementsByClassName("card-text")[0]
      card_text.setAttribute("stroke", "red");
      card_text.setAttribute("fill", "red");
    }
  }

  function update_button(config) {
    let button_background = document.getElementById(`button-background-${config["button"]}`)
    button_background.setAttribute("fill", "url(#dealer)");
  }

  function update_pot(config) {
    let pot = document.getElementById("pot-text");
    pot.innerHTML = config["pot"];
  }

  function update_street_commit(config) {
    for (let player_idx = 0; player_idx < config["street_commits"].length; player_idx++) {
      let street_commit = config["street_commits"][player_idx];
      document.getElementById(`street-commit-text-${player_idx}`).innerHTML = street_commit;
    }
  }

  socket.on('config', function (config) {
    reset_player();
    reset_community();
    reset_button();

    if (config.hasOwnProperty("hole_cards")) {
      update_cards(config);
      update_button(config);
      update_pot(config);
      update_street_commit(config);
    }
  })
})()